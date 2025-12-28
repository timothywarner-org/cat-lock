//! Build script for PawGate
//!
//! Embeds Windows resources (icon, manifest) into the executable

fn main() {
    // Only compile resources on Windows
    #[cfg(windows)]
    {
        embed_resource::compile("resources/pawgate.rc", embed_resource::NONE);
    }

    // Re-run if resource files change
    println!("cargo:rerun-if-changed=resources/pawgate.rc");
    println!("cargo:rerun-if-changed=resources/pawgate.manifest");
}
