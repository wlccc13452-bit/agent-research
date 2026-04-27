/**
 * React Error Boundary 组件
 * 
 * 功能：
 * 1. 捕获子组件树中的 JavaScript 错误
 * 2. 记录错误日志
 * 3. 显示友好的错误界面
 * 4. 提供重试机制
 */
import { Component } from 'react'
import type { ErrorInfo, ReactNode } from 'react'

interface Props {
  children: ReactNode
  fallback?: ReactNode
}

interface State {
  hasError: boolean
  error: Error | null
  errorInfo: ErrorInfo | null
}

class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props)
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null
    }
  }

  static getDerivedStateFromError(error: Error): Partial<State> {
    // 更新 state 以便下一次渲染能够显示降级后的 UI
    return { hasError: true, error }
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo): void {
    // 记录错误日志
    console.error('ErrorBoundary caught an error:', error)
    console.error('Error info:', errorInfo)
    
    // 更新状态
    this.setState({ errorInfo })
    
    // 可以将错误日志上报到服务器
    this.logErrorToService(error, errorInfo)
  }

  logErrorToService = (error: Error, errorInfo: ErrorInfo): void => {
    // 发送错误日志到后端
    fetch('/api/client-logs/log-error', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        error: {
          message: error.message,
          stack: error.stack
        },
        errorInfo: {
          componentStack: errorInfo.componentStack
        },
        timestamp: new Date().toISOString(),
        userAgent: navigator.userAgent,
        url: window.location.href
      })
    }).catch(err => {
      console.error('Failed to log error:', err)
    })
  }

  handleRetry = (): void => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null
    })
  }

  handleReload = (): void => {
    window.location.reload()
  }

  render(): ReactNode {
    if (this.state.hasError) {
      // 如果提供了自定义降级 UI，使用它
      if (this.props.fallback) {
        return this.props.fallback
      }

      // 默认错误界面
      return (
        <div style={{
          padding: '40px',
          textAlign: 'center',
          minHeight: '400px',
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'center',
          alignItems: 'center',
          backgroundColor: '#f5f5f5',
          borderRadius: '8px'
        }}>
          <div style={{
            fontSize: '48px',
            marginBottom: '20px'
          }}>
            😵
          </div>
          
          <h2 style={{
            fontSize: '24px',
            color: '#333',
            marginBottom: '16px'
          }}>
            出错了
          </h2>
          
          <p style={{
            fontSize: '16px',
            color: '#666',
            marginBottom: '24px',
            maxWidth: '600px'
          }}>
            很抱歉，应用程序遇到了一个错误。请尝试刷新页面或联系技术支持。
          </p>

          {import.meta.env.DEV && this.state.error && (
            <details style={{
              marginBottom: '24px',
              textAlign: 'left',
              maxWidth: '800px',
              width: '100%'
            }}>
              <summary style={{
                cursor: 'pointer',
                color: '#999',
                fontSize: '14px',
                marginBottom: '8px'
              }}>
                错误详情（仅开发环境可见）
              </summary>
              <pre style={{
                backgroundColor: '#fff',
                padding: '16px',
                borderRadius: '4px',
                overflow: 'auto',
                fontSize: '12px',
                color: '#d32f2f',
                border: '1px solid #e0e0e0'
              }}>
                {this.state.error.toString()}
                {'\n\n'}
                {this.state.errorInfo?.componentStack}
              </pre>
            </details>
          )}

          <div style={{
            display: 'flex',
            gap: '12px'
          }}>
            <button
              onClick={this.handleRetry}
              style={{
                padding: '10px 24px',
                fontSize: '16px',
                backgroundColor: '#1976d2',
                color: '#fff',
                border: 'none',
                borderRadius: '4px',
                cursor: 'pointer',
                transition: 'background-color 0.2s'
              }}
              onMouseOver={(e) => {
                e.currentTarget.style.backgroundColor = '#1565c0'
              }}
              onMouseOut={(e) => {
                e.currentTarget.style.backgroundColor = '#1976d2'
              }}
            >
              重试
            </button>
            
            <button
              onClick={this.handleReload}
              style={{
                padding: '10px 24px',
                fontSize: '16px',
                backgroundColor: '#fff',
                color: '#1976d2',
                border: '1px solid #1976d2',
                borderRadius: '4px',
                cursor: 'pointer',
                transition: 'background-color 0.2s'
              }}
              onMouseOver={(e) => {
                e.currentTarget.style.backgroundColor = '#f5f5f5'
              }}
              onMouseOut={(e) => {
                e.currentTarget.style.backgroundColor = '#fff'
              }}
            >
              刷新页面
            </button>
          </div>
        </div>
      )
    }

    return this.props.children
  }
}

export default ErrorBoundary
