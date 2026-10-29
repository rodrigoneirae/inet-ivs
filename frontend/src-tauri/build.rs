fn main() {
    tauri_build::try_build(
        tauri_build::Attributes::new().app_manifest(
            tauri_build::AppManifest::new().commands(&["guardar-archivo"]),
        ),
    )
    .expect("no se pudo ejecutar tauri-build");
}
