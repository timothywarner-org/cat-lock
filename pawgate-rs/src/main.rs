//! PawGate - Windows keyboard locking utility
//!
//! Prevents accidental keyboard input (e.g., from pets walking on keyboard).
//! Uses a configurable hotkey to toggle lock state.

#![windows_subsystem = "windows"]

mod config;
mod keyboard;
mod overlay;
mod tray;
mod settings_dialog;

use std::sync::atomic::{AtomicBool, Ordering};
use std::sync::Arc;
use log::{info, error};
use single_instance::SingleInstance;

/// Global state shared across threads
pub struct AppState {
    /// Whether keyboard is currently locked
    pub locked: AtomicBool,
    /// Signal to quit the application
    pub should_quit: AtomicBool,
    /// Signal to show settings dialog
    pub show_settings: AtomicBool,
}

impl AppState {
    pub fn new() -> Self {
        Self {
            locked: AtomicBool::new(false),
            should_quit: AtomicBool::new(false),
            show_settings: AtomicBool::new(false),
        }
    }
}

fn main() {
    // Initialize logging (only in debug builds)
    #[cfg(debug_assertions)]
    env_logger::init();

    info!("PawGate starting...");

    // Ensure single instance
    let instance = SingleInstance::new("pawgate-keyboard-locker").unwrap();
    if !instance.is_single() {
        error!("PawGate is already running!");
        show_error_message("PawGate is already running.\n\nCheck your system tray.");
        return;
    }

    // Load configuration
    let config = match config::Config::load() {
        Ok(c) => c,
        Err(e) => {
            error!("Failed to load config: {}", e);
            config::Config::default()
        }
    };

    info!("Loaded config: hotkey={}, opacity={}", config.hotkey, config.opacity);

    // Create shared state
    let state = Arc::new(AppState::new());

    // Start keyboard hook in background thread
    let kb_state = Arc::clone(&state);
    let kb_config = config.clone();
    let keyboard_thread = std::thread::spawn(move || {
        keyboard::run_keyboard_hook(kb_state, kb_config);
    });

    // Run the main UI loop (tray icon + overlay management)
    // This runs on the main thread to handle Windows messages properly
    if let Err(e) = tray::run_tray_loop(Arc::clone(&state), config) {
        error!("Tray loop error: {}", e);
    }

    // Signal keyboard thread to stop
    state.should_quit.store(true, Ordering::SeqCst);

    // Wait for keyboard thread to finish
    let _ = keyboard_thread.join();

    info!("PawGate exiting...");
}

/// Show a Windows error message box
fn show_error_message(msg: &str) {
    use windows::core::PCWSTR;
    use windows::Win32::UI::WindowsAndMessaging::{MessageBoxW, MB_ICONERROR, MB_OK};

    let wide_msg: Vec<u16> = msg.encode_utf16().chain(std::iter::once(0)).collect();
    let wide_title: Vec<u16> = "PawGate Error".encode_utf16().chain(std::iter::once(0)).collect();

    unsafe {
        MessageBoxW(
            None,
            PCWSTR(wide_msg.as_ptr()),
            PCWSTR(wide_title.as_ptr()),
            MB_OK | MB_ICONERROR,
        );
    }
}
