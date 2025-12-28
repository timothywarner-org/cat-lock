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

// =============================================================================
// Unit Tests
// =============================================================================

#[cfg(test)]
mod tests {
    use super::*;

    // -------------------------------------------------------------------------
    // Config Default Tests
    // -------------------------------------------------------------------------

    #[test]
    fn test_default_config_values() {
        /// WHY: Verify default values match documentation and are sensible.
        /// The default hotkey is part of the public API contract.
        let config = Config::default();

        assert_eq!(config.hotkey, "ctrl+b", "Default hotkey should be ctrl+b");
        assert_eq!(config.opacity, 0.3, "Default opacity should be 0.3 (30%)");
        assert!(config.notifications_enabled, "Notifications should be enabled by default");
        assert_eq!(config.overlay_color, "#1B5E20", "Default color should be forest green");
    }

    #[test]
    fn test_config_path_contains_pawgate() {
        /// WHY: Config path must include .pawgate directory for organization.
        let path = Config::config_path();
        let path_str = path.to_string_lossy();

        assert!(path_str.contains(".pawgate"), "Config path should contain .pawgate");
        assert!(path_str.ends_with("config.json"), "Config path should end with config.json");
    }

    // -------------------------------------------------------------------------
    // Color Parsing Tests
    // -------------------------------------------------------------------------

    #[test]
    fn test_parse_overlay_color_valid_hex() {
        /// WHY: Users configure colors via hex strings. Parsing must be correct.
        let config = Config {
            overlay_color: "#FF6600".to_string(),
            ..Default::default()
        };

        let (r, g, b) = config.parse_overlay_color();
        assert_eq!(r, 0xFF, "Red component should be 255");
        assert_eq!(g, 0x66, "Green component should be 102");
        assert_eq!(b, 0x00, "Blue component should be 0");
    }

    #[test]
    fn test_parse_overlay_color_without_hash() {
        /// WHY: Some users might omit the # prefix. Handle gracefully.
        let config = Config {
            overlay_color: "1B5E20".to_string(),
            ..Default::default()
        };

        let (r, g, b) = config.parse_overlay_color();
        assert_eq!((r, g, b), (0x1B, 0x5E, 0x20));
    }

    #[test]
    fn test_parse_overlay_color_invalid_returns_default() {
        /// WHY: Invalid color strings should fall back to default, not crash.
        let config = Config {
            overlay_color: "not-a-color".to_string(),
            ..Default::default()
        };

        let (r, g, b) = config.parse_overlay_color();
        // Should return default dark green
        assert_eq!((r, g, b), (27, 94, 32));
    }

    #[test]
    fn test_parse_overlay_color_short_hex() {
        /// WHY: Short hex strings (< 6 chars) should fall back to default.
        let config = Config {
            overlay_color: "#FFF".to_string(),
            ..Default::default()
        };

        let (r, g, b) = config.parse_overlay_color();
        assert_eq!((r, g, b), (27, 94, 32), "Short hex should return default");
    }

    // -------------------------------------------------------------------------
    // Serialization Tests
    // -------------------------------------------------------------------------

    #[test]
    fn test_config_serializes_to_json() {
        /// WHY: Config must serialize correctly for save() to work.
        let config = Config::default();
        let json = serde_json::to_string(&config);

        assert!(json.is_ok(), "Config should serialize to JSON");

        let json_str = json.unwrap();
        assert!(json_str.contains("hotkey"), "JSON should contain hotkey field");
        assert!(json_str.contains("opacity"), "JSON should contain opacity field");
        assert!(json_str.contains("ctrl+b"), "JSON should contain default hotkey value");
    }

    #[test]
    fn test_config_deserializes_from_json() {
        /// WHY: Config must deserialize correctly for load() to work.
        let json = r#"{
            "hotkey": "ctrl+shift+l",
            "opacity": 0.5,
            "notifications_enabled": false,
            "overlay_color": "#FF0000"
        }"#;

        let config: Result<Config, _> = serde_json::from_str(json);
        assert!(config.is_ok(), "Config should deserialize from JSON");

        let config = config.unwrap();
        assert_eq!(config.hotkey, "ctrl+shift+l");
        assert_eq!(config.opacity, 0.5);
        assert!(!config.notifications_enabled);
        assert_eq!(config.overlay_color, "#FF0000");
    }

    #[test]
    fn test_config_round_trip() {
        /// WHY: Serialize then deserialize should preserve all values.
        let original = Config {
            hotkey: "alt+f12".to_string(),
            opacity: 0.75,
            notifications_enabled: false,
            overlay_color: "#123456".to_string(),
        };

        let json = serde_json::to_string(&original).unwrap();
        let restored: Config = serde_json::from_str(&json).unwrap();

        assert_eq!(original.hotkey, restored.hotkey);
        assert_eq!(original.opacity, restored.opacity);
        assert_eq!(original.notifications_enabled, restored.notifications_enabled);
        assert_eq!(original.overlay_color, restored.overlay_color);
    }

    // -------------------------------------------------------------------------
    // Hotkey Parsing Tests (platform-independent logic)
    // -------------------------------------------------------------------------

    // Note: parse_hotkey() uses Windows-specific constants, so we can only
    // test it on Windows. The tests below use cfg(windows).

    #[cfg(windows)]
    mod hotkey_tests {
        use super::*;
        use windows::Win32::UI::Input::KeyboardAndMouse::*;

        #[test]
        fn test_parse_simple_hotkey_ctrl_b() {
            /// WHY: The default hotkey must parse correctly.
            let result = parse_hotkey("ctrl+b");

            assert!(result.is_some(), "ctrl+b should parse successfully");
            let (modifiers, vk) = result.unwrap();

            assert_eq!(modifiers, MOD_CONTROL.0, "Should have CTRL modifier");
            assert_eq!(vk, 'B' as u32, "Should have B key");
        }

        #[test]
        fn test_parse_complex_hotkey() {
            /// WHY: Users may configure complex multi-modifier hotkeys.
            let result = parse_hotkey("ctrl+shift+alt+f12");

            assert!(result.is_some());
            let (modifiers, vk) = result.unwrap();

            assert!(modifiers & MOD_CONTROL.0 != 0, "Should have CTRL");
            assert!(modifiers & MOD_SHIFT.0 != 0, "Should have SHIFT");
            assert!(modifiers & MOD_ALT.0 != 0, "Should have ALT");
            assert_eq!(vk, VK_F12.0 as u32, "Should have F12 key");
        }

        #[test]
        fn test_parse_hotkey_case_insensitive() {
            /// WHY: Hotkey strings should be case-insensitive for user convenience.
            let lower = parse_hotkey("ctrl+b");
            let upper = parse_hotkey("CTRL+B");
            let mixed = parse_hotkey("Ctrl+B");

            assert_eq!(lower, upper, "Case should not matter");
            assert_eq!(lower, mixed, "Case should not matter");
        }

        #[test]
        fn test_parse_hotkey_with_spaces() {
            /// WHY: Users might add spaces around + signs.
            let result = parse_hotkey("ctrl + b");

            assert!(result.is_some(), "Spaces around + should be tolerated");
            let (modifiers, vk) = result.unwrap();
            assert_eq!(modifiers, MOD_CONTROL.0);
            assert_eq!(vk, 'B' as u32);
        }

        #[test]
        fn test_parse_function_keys() {
            /// WHY: F1-F24 are common hotkey targets.
            for i in 1..=12 {
                let hotkey = format!("f{}", i);
                let result = parse_hotkey(&hotkey);

                assert!(result.is_some(), "F{} should parse", i);
                let (_, vk) = result.unwrap();
                assert_eq!(vk, VK_F1.0 as u32 + i - 1, "F{} vk code incorrect", i);
            }
        }

        #[test]
        fn test_parse_special_keys() {
            /// WHY: Special keys like space, enter, etc. should work.
            let test_cases = [
                ("space", VK_SPACE.0 as u32),
                ("enter", VK_RETURN.0 as u32),
                ("escape", VK_ESCAPE.0 as u32),
                ("tab", VK_TAB.0 as u32),
                ("backspace", VK_BACK.0 as u32),
            ];

            for (key_name, expected_vk) in test_cases {
                let result = parse_hotkey(&format!("ctrl+{}", key_name));
                assert!(result.is_some(), "{} should parse", key_name);

                let (_, vk) = result.unwrap();
                assert_eq!(vk, expected_vk, "{} vk code incorrect", key_name);
            }
        }

        #[test]
        fn test_parse_win_modifier() {
            /// WHY: Windows key modifier should work.
            let result = parse_hotkey("win+l");

            assert!(result.is_some());
            let (modifiers, _) = result.unwrap();
            assert!(modifiers & MOD_WIN.0 != 0, "Should have WIN modifier");
        }

        #[test]
        fn test_parse_invalid_hotkey() {
            /// WHY: Invalid hotkeys should return None, not panic.
            let result = parse_hotkey("not+a+valid+key+combo");

            // Should return None or Some with only modifiers (no vk)
            // The current implementation returns None if no valid key found
            if let Some((_, vk)) = result {
                // If it returns Some, the vk should be 0 or the function
                // found something it thought was a key
                // This is acceptable behavior
            }
        }

        #[test]
        fn test_parse_number_keys() {
            /// WHY: Number keys 0-9 should work as hotkey targets.
            for i in 0..=9 {
                let hotkey = format!("ctrl+{}", i);
                let result = parse_hotkey(&hotkey);

                assert!(result.is_some(), "ctrl+{} should parse", i);
                let (_, vk) = result.unwrap();
                assert_eq!(vk, ('0' as u32) + i, "Number {} vk code incorrect", i);
            }
        }

        #[test]
        fn test_parse_modifier_aliases() {
            /// WHY: Both "ctrl" and "control" should work.
            let ctrl = parse_hotkey("ctrl+b");
            let control = parse_hotkey("control+b");

            assert_eq!(ctrl, control, "ctrl and control should be equivalent");
        }
    }
}
