const std = @import("std");

pub fn main() !void {
    var gpa = std.heap.GeneralPurposeAllocator(.{}){};
    defer _ = gpa.deinit();
    const allocator = gpa.allocator();

    const address = try std.net.Address.parseIp4("0.0.0.0", 8080);
    var server = try address.listen(.{ .reuse_address = true });
    defer server.deinit();

    std.log.info("Stock server listening on http://0.0.0.0:8080", .{});

    while (true) {
        var conn = try server.accept();
        defer conn.stream.close();

        handleConnection(allocator, &conn) catch |err| {
            std.log.err("failed to handle connection: {s}", .{@errorName(err)});
        };
    }
}

fn handleConnection(allocator: std.mem.Allocator, conn: *std.net.Server.Connection) !void {
    var reader_buffer: [1024]u8 = undefined;
    var stream_reader = conn.stream.reader(&reader_buffer);
    var buffer: [8192]u8 = undefined;
    var read_targets: [1][]u8 = .{buffer[0..]};
    const read_len = stream_reader.interface().readVec(&read_targets) catch |err| switch (err) {
        error.EndOfStream => 0,
        error.ReadFailed => return stream_reader.getError() orelse error.Unexpected,
    };
    if (read_len == 0) return;

    const request = buffer[0..read_len];
    const line_end = std.mem.indexOf(u8, request, "\r\n") orelse return sendText(allocator, conn.stream, "400 Bad Request", "invalid request");
    const request_line = request[0..line_end];

    var parts = std.mem.tokenizeScalar(u8, request_line, ' ');
    const method = parts.next() orelse return sendText(allocator, conn.stream, "400 Bad Request", "invalid method");
    const target = parts.next() orelse return sendText(allocator, conn.stream, "400 Bad Request", "invalid target");

    if (!std.mem.eql(u8, method, "GET")) {
        return sendText(allocator, conn.stream, "405 Method Not Allowed", "only GET is supported");
    }

    if (std.mem.eql(u8, target, "/health")) {
        return sendJson(allocator, conn.stream, "200 OK", "{\"status\":\"ok\"}");
    }

    const split = splitTarget(target);
    const path = split.path;
    const query = split.query;

    if (std.mem.eql(u8, path, "/api/v1/quote")) {
        const symbol = getQueryParam(query, "symbol") orelse "000001.SZ";
        return sendQuote(allocator, conn.stream, symbol);
    }

    return sendText(allocator, conn.stream, "404 Not Found", "route not found");
}

fn splitTarget(target: []const u8) struct { path: []const u8, query: []const u8 } {
    const query_mark = std.mem.indexOfScalar(u8, target, '?') orelse {
        return .{ .path = target, .query = "" };
    };
    return .{ .path = target[0..query_mark], .query = target[query_mark + 1 ..] };
}

fn getQueryParam(query: []const u8, key: []const u8) ?[]const u8 {
    var query_parts = std.mem.tokenizeScalar(u8, query, '&');
    while (query_parts.next()) |entry| {
        const equal_index = std.mem.indexOfScalar(u8, entry, '=') orelse continue;
        const k = entry[0..equal_index];
        const v = entry[equal_index + 1 ..];
        if (std.mem.eql(u8, k, key) and v.len > 0) {
            return v;
        }
    }
    return null;
}

fn sendQuote(allocator: std.mem.Allocator, stream: std.net.Stream, symbol: []const u8) !void {
    const now = std.time.timestamp();
    const price = mockPrice(symbol);
    const change = price * 0.0075;

    const body = try std.fmt.allocPrint(
        allocator,
        "{{\"symbol\":\"{s}\",\"price\":{d:.2},\"change\":{d:.2},\"currency\":\"CNY\",\"timestamp\":{d}}}",
        .{ symbol, price, change, now },
    );
    defer allocator.free(body);

    try sendJson(allocator, stream, "200 OK", body);
}

fn mockPrice(symbol: []const u8) f64 {
    var hash: u32 = 2166136261;
    for (symbol) |ch| {
        hash ^= ch;
        hash *%= 16777619;
    }
    const raw = @as(f64, @floatFromInt(hash % 5000));
    return 5.0 + raw / 100.0;
}

fn sendJson(allocator: std.mem.Allocator, stream: std.net.Stream, status: []const u8, body: []const u8) !void {
    const response = try std.fmt.allocPrint(
        allocator,
        "HTTP/1.1 {s}\r\nContent-Type: application/json; charset=utf-8\r\nContent-Length: {d}\r\nConnection: close\r\n\r\n{s}",
        .{ status, body.len, body },
    );
    defer allocator.free(response);
    try stream.writeAll(response);
}

fn sendText(allocator: std.mem.Allocator, stream: std.net.Stream, status: []const u8, body: []const u8) !void {
    const response = try std.fmt.allocPrint(
        allocator,
        "HTTP/1.1 {s}\r\nContent-Type: text/plain; charset=utf-8\r\nContent-Length: {d}\r\nConnection: close\r\n\r\n{s}",
        .{ status, body.len, body },
    );
    defer allocator.free(response);
    try stream.writeAll(response);
}

test "split target" {
    const a = splitTarget("/api/v1/quote");
    try std.testing.expectEqualStrings("/api/v1/quote", a.path);
    try std.testing.expectEqualStrings("", a.query);

    const b = splitTarget("/api/v1/quote?symbol=600519.SH");
    try std.testing.expectEqualStrings("/api/v1/quote", b.path);
    try std.testing.expectEqualStrings("symbol=600519.SH", b.query);
}

test "query param parser" {
    const symbol = getQueryParam("symbol=000001.SZ&market=cn", "symbol") orelse "";
    try std.testing.expectEqualStrings("000001.SZ", symbol);
}
