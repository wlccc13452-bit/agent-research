class SnakeGame {
    constructor() {
        this.canvas = document.getElementById('gameCanvas');
        this.ctx = this.canvas.getContext('2d');
        this.scoreElement = document.getElementById('score');
        this.gameOverElement = document.getElementById('gameOver');
        
        // Game settings
        this.gridSize = 20;
        this.tileCount = this.canvas.width / this.gridSize;
        
        // Game state
        this.snake = [
            {x: 10, y: 10}
        ];
        this.food = this.generateFood();
        this.dx = 0;
        this.dy = 0;
        this.score = 0;
        this.gameRunning = true;
        
        // Bind methods
        this.handleKeyPress = this.handleKeyPress.bind(this);
        this.gameLoop = this.gameLoop.bind(this);
        
        // Initialize game
        this.init();
    }
    
    init() {
        document.addEventListener('keydown', this.handleKeyPress);
        this.drawGame();
        this.update();
    }
    
    handleKeyPress(event) {
        if (!this.gameRunning && event.keyCode === 32) {
            // Space bar to restart
            this.restart();
            return;
        }
        
        if (!this.gameRunning) return;
        
        const goingUp = this.dy === -1;
        const goingDown = this.dy === 1;
        const goingRight = this.dx === 1;
        const goingLeft = this.dx === -1;
        
        if (event.keyCode === 37 && !goingRight) { // Left arrow
            this.dx = -1;
            this.dy = 0;
        }
        if (event.keyCode === 38 && !goingDown) { // Up arrow
            this.dx = 0;
            this.dy = -1;
        }
        if (event.keyCode === 39 && !goingLeft) { // Right arrow
            this.dx = 1;
            this.dy = 0;
        }
        if (event.keyCode === 40 && !goingUp) { // Down arrow
            this.dx = 0;
            this.dy = 1;
        }
    }
    
    update() {
        if (!this.gameRunning) return;
        
        setTimeout(() => {
            this.clearCanvas();
            this.moveSnake();
            
            if (this.checkGameOver()) {
                this.gameOver();
                return;
            }
            
            this.checkFoodCollision();
            this.drawGame();
            this.update();
        }, 100);
    }
    
    clearCanvas() {
        this.ctx.fillStyle = '#111';
        this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);
    }
    
    moveSnake() {
        const head = {x: this.snake[0].x + this.dx, y: this.snake[0].y + this.dy};
        this.snake.unshift(head);
        
        // Remove tail if no food eaten
        if (head.x !== this.food.x || head.y !== this.food.y) {
            this.snake.pop();
        }
    }
    
    checkFoodCollision() {
        const head = this.snake[0];
        if (head.x === this.food.x && head.y === this.food.y) {
            this.score += 10;
            this.scoreElement.textContent = this.score;
            this.food = this.generateFood();
        }
    }
    
    checkGameOver() {
        const head = this.snake[0];
        
        // Check wall collision
        if (head.x < 0 || head.x >= this.tileCount || head.y < 0 || head.y >= this.tileCount) {
            return true;
        }
        
        // Check self collision
        for (let i = 1; i < this.snake.length; i++) {
            if (head.x === this.snake[i].x && head.y === this.snake[i].y) {
                return true;
            }
        }
        
        return false;
    }
    
    generateFood() {
        let food;
        do {
            food = {
                x: Math.floor(Math.random() * this.tileCount),
                y: Math.floor(Math.random() * this.tileCount)
            };
        } while (this.snake.some(segment => segment.x === food.x && segment.y === food.y));
        
        return food;
    }
    
    drawGame() {
        this.drawSnake();
        this.drawFood();
    }
    
    drawSnake() {
        this.ctx.fillStyle = '#4CAF50';
        this.snake.forEach((segment, index) => {
            // Make head slightly different
            if (index === 0) {
                this.ctx.fillStyle = '#66BB6A';
            } else {
                this.ctx.fillStyle = '#4CAF50';
            }
            this.ctx.fillRect(segment.x * this.gridSize, segment.y * this.gridSize, this.gridSize - 2, this.gridSize - 2);
        });
    }
    
    drawFood() {
        this.ctx.fillStyle = '#FF5252';
        this.ctx.fillRect(this.food.x * this.gridSize, this.food.y * this.gridSize, this.gridSize - 2, this.gridSize - 2);
    }
    
    gameOver() {
        this.gameRunning = false;
        this.gameOverElement.style.display = 'block';
    }
    
    restart() {
        this.snake = [{x: 10, y: 10}];
        this.food = this.generateFood();
        this.dx = 0;
        this.dy = 0;
        this.score = 0;
        this.scoreElement.textContent = this.score;
        this.gameRunning = true;
        this.gameOverElement.style.display = 'none';
        this.update();
    }
}

// Start the game when the page loads
window.addEventListener('load', () => {
    new SnakeGame();
});