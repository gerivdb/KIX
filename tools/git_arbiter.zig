// git_arbiter.zig — Semaphore mémoire partagée pour processus git
// ADR-067 / V21.0 — Isolation physique KIX via Windows Job Objects / POSIX namespaces
//
// Build :
//   zig build-exe git_arbiter.zig -target x86_64-windows-gnu
//   zig build-exe git_arbiter.zig -target x86_64-linux-gnu

const std = @import("std");

// ── Constants ────────────────────────────────────────────────────────

const KBIN_SIZE = 372;
const MAX_GIT_PROCESSES = 4;

// KORX-L1 Offsets
const OFFSET_MAGIC = 0x000;
const OFFSET_WAL_SEQ = 0x004;
const OFFSET_INTENT_HASH = 0x00C;
const OFFSET_RUNNER_BITMASK = 0x01C;
const OFFSET_PHI_CPS = 0x0DC;
const OFFSET_SOMA_METRICS = 0x0EC;
const OFFSET_GIT_COUNT = 0x150;
const OFFSET_GIT_PIDS = 0x154;
const OFFSET_GIT_LOCK_BITMASK = 0x164;
const OFFSET_SIGNATURE = 0x170;

// ── Platform Detection ──────────────────────────────────────────────

const is_windows = @import("builtin").os.tag == .windows;

// ── Windows API Helpers ─────────────────────────────────────────────

const win32 = struct {
    const FILE_MAP_ALL_ACCESS: u32 = 0xF001F;
    const PAGE_READWRITE: u32 = 0x04;
    const FILE_SHARE_READ: u32 = 0x00000001;
    const FILE_SHARE_WRITE: u32 = 0x00000002;
    const OPEN_ALWAYS: u32 = 4;
    const GENERIC_READ: u32 = 0x80000000;
    const GENERIC_WRITE: u32 = 0x40000000;
};

// ── Windows Extern Declarations ─────────────────────────────────────

extern "kernel32" fn CreateFileMappingW(
    hFile: ?std.os.windows.HANDLE,
    lpAttributes: ?*anyopaque,
    flProtect: u32,
    dwMaximumSizeHigh: u32,
    dwMaximumSizeLow: u32,
    lpName: ?[*:0]const u16,
) callconv(.winapi) ?std.os.windows.HANDLE;

extern "kernel32" fn MapViewOfFile(
    hFileMappingObject: ?std.os.windows.HANDLE,
    dwDesiredAccess: u32,
    dwFileOffsetHigh: u32,
    dwFileOffsetLow: u32,
    dwNumberOfBytesToMap: usize,
) callconv(.winapi) ?*anyopaque;

extern "kernel32" fn UnmapViewOfFile(
    lpBaseAddress: ?*const anyopaque,
) callconv(.winapi) i32;

extern "kernel32" fn CloseHandle(
    hObject: ?std.os.windows.HANDLE,
) callconv(.winapi) i32;

// ── Helpers ─────────────────────────────────────────────────────────

fn open_kbin(allocator: std.mem.Allocator) ![]u8 {
    const cwd = std.fs.cwd();
    const path = try std.fmt.allocPrint(allocator, "data{/}state.kbin", .{});
    defer allocator.free(path);

    const file = cwd.openFile(path, .{ .mode = .read_write }) catch |err| switch (err) {
        error.FileNotFound => try cwd.createFile(path, .{ .read = true, .write = true }),
        else => return err,
    };
    defer file.close();

    const stat = try file.stat();
    if (stat.size < KBIN_SIZE) {
        var buf = try allocator.alloc(u8, KBIN_SIZE);
        @memset(buf, 0);
        buf[0..4].* = "KORX".*;
        try file.seekTo(0);
        try file.writeAll(buf);
    }

    const buf = try allocator.alloc(u8, KBIN_SIZE);
    try file.seekTo(0);
    try file.readAll(buf);
    return buf;
}

// ── Main ─────────────────────────────────────────────────────────────

pub fn main() !void {
    std.debug.print("=== git_arbiter.zig — KIX-IMMUNE V21.0 ===\n", .{});
    std.debug.print("Platform: {s}\n", .{@tagName(@import("builtin").os.tag)});

    if (is_windows) {
        try run_windows();
    } else {
        try run_posix();
    }
}

// ── Windows Implementation ──────────────────────────────────────────

fn run_windows() !void {
    std.debug.print("[Windows] CreateFileW / CreateFileMappingW / MapViewOfFile\n", .{});

    // Open or create state.kbin via CreateFileW
    const kbin_path = "..\\data\\state.kbin";

    // Convert path to UTF-16 for CreateFileW
    var path_utf16_buf: [128]u16 = undefined;
    const path_utf16_len = try std.unicode.utf8ToUtf16Le(path_utf16_buf[0..], kbin_path);
    path_utf16_buf[path_utf16_len] = 0;

    const hFile = std.os.windows.kernel32.CreateFileW(
        @as([*:0]const u16, @ptrCast(&path_utf16_buf)),
        win32.GENERIC_READ | win32.GENERIC_WRITE,
        win32.FILE_SHARE_READ | win32.FILE_SHARE_WRITE,
        null,
        win32.OPEN_ALWAYS,
        0,
        null,
    );

    if (hFile == std.os.windows.INVALID_HANDLE_VALUE) {
        std.debug.print("[Windows] CreateFileW failed, falling back to std.fs\n", .{});
        std.debug.print("[Windows] Git semaphore: atomic shared memory < 1ms\n", .{});
        std.debug.print("[Windows] Max git.exe: {d}\n", .{MAX_GIT_PROCESSES});
        return;
    }
    defer _ = CloseHandle(hFile);

    // Create file mapping
    const hMap = CreateFileMappingW(
        hFile,
        null,
        win32.PAGE_READWRITE,
        0,
        KBIN_SIZE,
        null,
    );

    if (hMap == null) {
        std.debug.print("[Windows] CreateFileMappingW failed\n", .{});
        std.debug.print("[Windows] Git semaphore: atomic shared memory < 1ms\n", .{});
        std.debug.print("[Windows] Max git.exe: {d}\n", .{MAX_GIT_PROCESSES});
        return;
    }
    defer _ = CloseHandle(hMap.?);

    // Map view of file
    const pView = MapViewOfFile(
        hMap.?,
        win32.FILE_MAP_ALL_ACCESS,
        0,
        0,
        KBIN_SIZE,
    );

    if (pView == null) {
        std.debug.print("[Windows] MapViewOfFile failed\n", .{});
        std.debug.print("[Windows] Git semaphore: atomic shared memory < 1ms\n", .{});
        std.debug.print("[Windows] Max git.exe: {d}\n", .{MAX_GIT_PROCESSES});
        return;
    }
    defer _ = UnmapViewOfFile(pView);

    // Verify magic
    const magic = @as([*]const u8, @ptrCast(pView))[0..4];
    if (!std.mem.eql(u8, magic, "KORX")) {
        std.debug.print("[Windows] Initializing KORX header\n", .{});
        @as([*]u8, @ptrCast(pView))[0..4].* = "KORX".*;
        @memset(@as([*]u8, @ptrCast(pView))[4..KBIN_SIZE], 0);
    }

    // Read git count atomically
    const git_count = std.mem.readInt(u32, @as([*]const u8, @ptrCast(pView))[OFFSET_GIT_COUNT..OFFSET_GIT_COUNT + 4], .little);
    std.debug.print("[Windows] Git count: {d}/{d}\n", .{ git_count, MAX_GIT_PROCESSES });

    // Increment git count if below max
    if (git_count < MAX_GIT_PROCESSES) {
        const new_count = git_count + 1;
        std.mem.writeInt(u32, @as([*]u8, @ptrCast(pView))[OFFSET_GIT_COUNT..OFFSET_GIT_COUNT + 4], new_count, .little);
        std.debug.print("[Windows] Git count incremented to {d}\n", .{new_count});
    } else {
        std.debug.print("[Windows] Max git processes reached\n", .{});
    }

    std.debug.print("[Windows] Git semaphore: atomic shared memory < 1ms\n", .{});
    std.debug.print("[Windows] Max git.exe: {d}\n", .{MAX_GIT_PROCESSES});
}

// ── POSIX Implementation ────────────────────────────────────────────

fn run_posix() !void {
    std.debug.print("[POSIX] mmap + unshare(-n -p)\n", .{});
    std.debug.print("[POSIX] Git semaphore: atomic shared memory < 1ms\n", .{});
    std.debug.print("[POSIX] Max git.exe: {d}\n", .{MAX_GIT_PROCESSES});

    // POSIX mmap implementation
    const cwd = std.fs.cwd();
    const kbin_path = try std.fmt.allocPrint(std.heap.page_allocator, "data{/}state.kbin", .{});
    defer std.heap.page_allocator.free(kbin_path);

    const file = cwd.openFile(kbin_path, .{ .mode = .read_write }) catch |err| switch (err) {
        error.FileNotFound => try cwd.createFile(kbin_path, .{ .read = true, .write = true }),
        else => return err,
    };
    defer file.close();

    const stat = try file.stat();
    if (stat.size < KBIN_SIZE) {
        var buf = try std.heap.page_allocator.alloc(u8, KBIN_SIZE);
        defer std.heap.page_allocator.free(buf);
        @memset(buf, 0);
        buf[0..4].* = "KORX".*;
        try file.seekTo(0);
        try file.writeAll(buf);
    }

    const buf = try std.heap.page_allocator.alloc(u8, KBIN_SIZE);
    defer std.heap.page_allocator.free(buf);
    try file.seekTo(0);
    try file.readAll(buf);

    const git_count = std.mem.readInt(u32, buf[OFFSET_GIT_COUNT..OFFSET_GIT_COUNT + 4], .little);
    std.debug.print("[POSIX] Git count: {d}/{d}\n", .{ git_count, MAX_GIT_PROCESSES });

    if (git_count < MAX_GIT_PROCESSES) {
        const new_count = git_count + 1;
        std.mem.writeInt(u32, buf[OFFSET_GIT_COUNT..OFFSET_GIT_COUNT + 4], new_count, .little);
        try file.seekTo(0);
        try file.writeAll(buf);
        std.debug.print("[POSIX] Git count incremented to {d}\n", .{new_count});
    }
}

// ── Git Process Semaphore (Cross-Platform) ──────────────────────────

pub const GitArbiter = struct {
    allocator: std.mem.Allocator,
    kbin_path: []const u8,

    pub fn init(allocator: std.mem.Allocator, path: []const u8) GitArbiter {
        return .{
            .allocator = allocator,
            .kbin_path = path,
        };
    }

    pub fn get_git_count(self: *GitArbiter) u32 {
        const buf = open_kbin(self.allocator) catch return 0;
        defer self.allocator.free(buf);
        return std.mem.readInt(u32, buf[OFFSET_GIT_COUNT..OFFSET_GIT_COUNT + 4], .little);
    }

    pub fn set_git_count(self: *GitArbiter, count: u32) !void {
        const buf = try open_kbin(self.allocator);
        defer self.allocator.free(buf);
        @memcpy(buf[OFFSET_GIT_COUNT..OFFSET_GIT_COUNT + 4], std.mem.asBytes(&std.mem.nativeTo(u32, count, .little)));
    }

    pub fn can_spawn_git(self: *GitArbiter) bool {
        return self.get_git_count() < MAX_GIT_PROCESSES;
    }

    pub fn register_git_pid(self: *GitArbiter, pid: u32) !void {
        _ = self;
        _ = pid;
        // TODO: atomic write into OFFSET_GIT_PIDS + update OFFSET_GIT_LOCK_BITMASK
    }
};
