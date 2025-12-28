//! Configuration management for PawGate
//!
//! Stores settings in JSON format at ~/.pawgate/config.json

use serde::{Deserialize, Serialize};
use std::fs;
use std::path::PathBuf;

/// Application configuration
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Config {
    /// Hotkey to toggle lock (e.g., "ctrl+b", "ctrl+shift+l")
    pub hotkey: String,

    /// Overlay opacity (0.0 to 1.0)
    pub opacity: f32,

    /// Whether to show notifications
    pub notifications_enabled: bool,

    /// Overlay color in hex (e.g., "#2D5A27" for green)
    pub overlay_color: String,
}

impl Default for Config {
    fn default() -> Self {
        Self {
            hotkey: "ctrl+b".to_string(),
            opacity: 0.3,
            notifications_enabled: true,
            // Colorblind-friendly green that's distinguishable
            overlay_color: "#1B5E20".to_string(),
        }
    }
}

impl Config {
    /// Get the config file path (~/.pawgate/config.json)
    pub fn config_path() -> PathBuf {
        let home = dirs::home_dir().unwrap_or_else(|| PathBuf::from("."));
        home.join(".pawgate").join("config.json")
    }

    /// Load configuration from disk, or return default if not found
    pub fn load() -> Result<Self, Box<dyn std::error::Error>> {
        let path = Self::config_path();

        if !path.exists() {
            // Create default config
            let config = Self::default();
            config.save()?;
            return Ok(config);
        }

        let contents = fs::read_to_string(&path)?;
        let config: Config = serde_json::from_str(&contents)?;
        Ok(config)
    }

    /// Save configuration to disk
    pub fn save(&self) -> Result<(), Box<dyn std::error::Error>> {
        let path = Self::config_path();

        // Create parent directory if needed
        if let Some(parent) = path.parent() {
            fs::create_dir_all(parent)?;
        }

        let contents = serde_json::to_string_pretty(self)?;
        fs::write(&path, contents)?;
        Ok(())
    }

    /// Parse overlay color from hex string to RGB
    pub fn parse_overlay_color(&self) -> (u8, u8, u8) {
        let hex = self.overlay_color.trim_start_matches('#');
        if hex.len() == 6 {
            if let (Ok(r), Ok(g), Ok(b)) = (
                u8::from_str_radix(&hex[0..2], 16),
                u8::from_str_radix(&hex[2..4], 16),
                u8::from_str_radix(&hex[4..6], 16),
            ) {
                return (r, g, b);
            }
        }
        // Default to dark green if parsing fails
        (27, 94, 32)
    }
}

/// Parse hotkey string into modifier flags and virtual key code
/// Returns (modifiers, vk_code) where modifiers is a bitmask
pub fn parse_hotkey(hotkey: &str) -> Option<(u32, u32)> {
    use windows::Win32::UI::Input::KeyboardAndMouse::*;

    let parts: Vec<&str> = hotkey.to_lowercase().split('+').map(|s| s.trim()).collect();

    let mut modifiers: u32 = 0;
    let mut vk_code: Option<u32> = None;

    for part in parts {
        match part {
            "ctrl" | "control" => modifiers |= MOD_CONTROL.0,
            "alt" => modifiers |= MOD_ALT.0,
            "shift" => modifiers |= MOD_SHIFT.0,
            "win" | "windows" => modifiers |= MOD_WIN.0,
            // Single letter keys
            key if key.len() == 1 => {
                let c = key.chars().next().unwrap().to_ascii_uppercase();
                if c.is_ascii_alphabetic() {
                    vk_code = Some(c as u32);
                } else if c.is_ascii_digit() {
                    vk_code = Some(c as u32);
                }
            }
            // Function keys
            key if key.starts_with('f') && key.len() <= 3 => {
                if let Ok(num) = key[1..].parse::<u32>() {
                    if num >= 1 && num <= 24 {
                        vk_code = Some(VK_F1.0 as u32 + num - 1);
                    }
                }
            }
            // Special keys
            "space" => vk_code = Some(VK_SPACE.0 as u32),
            "enter" | "return" => vk_code = Some(VK_RETURN.0 as u32),
            "escape" | "esc" => vk_code = Some(VK_ESCAPE.0 as u32),
            "tab" => vk_code = Some(VK_TAB.0 as u32),
            "backspace" => vk_code = Some(VK_BACK.0 as u32),
            "delete" | "del" => vk_code = Some(VK_DELETE.0 as u32),
            "insert" | "ins" => vk_code = Some(VK_INSERT.0 as u32),
            "home" => vk_code = Some(VK_HOME.0 as u32),
            "end" => vk_code = Some(VK_END.0 as u32),
            "pageup" | "pgup" => vk_code = Some(VK_PRIOR.0 as u32),
            "pagedown" | "pgdn" => vk_code = Some(VK_NEXT.0 as u32),
            "up" => vk_code = Some(VK_UP.0 as u32),
            "down" => vk_code = Some(VK_DOWN.0 as u32),
            "left" => vk_code = Some(VK_LEFT.0 as u32),
            "right" => vk_code = Some(VK_RIGHT.0 as u32),
            "numlock" => vk_code = Some(VK_NUMLOCK.0 as u32),
            "scrolllock" => vk_code = Some(VK_SCROLL.0 as u32),
            "pause" => vk_code = Some(VK_PAUSE.0 as u32),
            "printscreen" | "prtsc" => vk_code = Some(VK_SNAPSHOT.0 as u32),
            _ => {}
        }
    }

    vk_code.map(|vk| (modifiers, vk))
}
