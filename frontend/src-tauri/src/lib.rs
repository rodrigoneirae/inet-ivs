use std::fs;
use std::path::PathBuf;

use base64::engine::general_purpose::STANDARD as BASE64;
use base64::Engine;
use tauri_plugin_dialog::DialogExt;

/// Orígenes autorizados a solicitar el guardado de un archivo.
const ORIGENES_PERMITIDOS: [(&str, &str, Option<u16>); 5] = [
    ("https", "inet-ivs.inversierra.cl", None),
    ("tauri", "localhost", None),
    ("http", "tauri.localhost", None),
    ("http", "127.0.0.1", Some(4321)),
    ("http", "localhost", Some(4321)),
];

/// El origen se compara por esquema, host y puerto; no por prefijo de texto.
fn origen_permitido(url: &tauri::Url) -> bool {
    let esquema = url.scheme();
    let host = url.host_str().unwrap_or_default();
    let puerto = url.port();
    ORIGENES_PERMITIDOS
        .iter()
        .any(|(esquema_permitido, host_permitido, puerto_permitido)| {
            let coincide_puerto = match puerto_permitido {
                None => true,
                Some(permitido) => puerto == Some(*permitido),
            };
            esquema == *esquema_permitido
                && host.eq_ignore_ascii_case(host_permitido)
                && coincide_puerto
        })
}

/// Guarda el contenido recibido en la ruta que el usuario elija.
#[tauri::command(rename = "guardar-archivo")]
async fn guardar_archivo(
    app: tauri::AppHandle,
    webview: tauri::Webview,
    nombre: String,
    contenido: String,
) -> Result<Option<String>, String> {
    let url = webview
        .url()
        .map_err(|_| "No se pudo determinar el origen de la solicitud.".to_string())?;
    if !origen_permitido(&url) {
        return Err("El origen de la solicitud no está autorizado.".to_string());
    }

    // El nombre lo decide la aplicación, nunca el contenido de la página.
    let nombre = sanitizar_nombre(&nombre);
    let bytes = BASE64
        .decode(contenido.as_bytes())
        .map_err(|_| "El contenido recibido no es válido.".to_string())?;

    let (enviar, mut recibir) = tauri::async_runtime::channel(1);
    app.dialog()
        .file()
        .add_filter("Excel", &["xlsx"])
        .set_file_name(&nombre)
        .save_file(move |ruta| {
            let _ = enviar.send(ruta);
        });

    let ruta = recibir
        .recv()
        .await
        .ok_or("No se pudo abrir el diálogo de guardado.".to_string())?;
    let Some(ruta) = ruta else {
        return Ok(None);
    };
    let ruta: PathBuf = ruta
        .into_path()
        .map_err(|_| "La ruta indicada no es válida.".to_string())?;

    fs::write(&ruta, bytes).map_err(|error| format!("No se pudo escribir el archivo: {error}"))?;
    Ok(Some(ruta.to_string_lossy().to_string()))
}

/// Impide que el nombre incluya rutas o caracteres fuera de lo esperado.
fn sanitizar_nombre(nombre: &str) -> String {
    let base = nombre
        .rsplit(['/', '\\'])
        .next()
        .unwrap_or("pedidos.xlsx")
        .trim()
        .to_lowercase();
    let limpio: String = base
        .chars()
        .filter(|caracter| caracter.is_ascii_alphanumeric() || *caracter == '.' || *caracter == '-')
        .collect();
    let limpio = if limpio.is_empty() { "pedidos.xlsx".to_string() } else { limpio };
    if limpio.ends_with(".xlsx") {
        limpio
    } else {
        format!("{limpio}.xlsx")
    }
}

/// Inicia la aplicación de escritorio de INET IVS.
#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_dialog::init())
        .invoke_handler(tauri::generate_handler![guardar_archivo])
        .run(tauri::generate_context!())
        .expect("No se pudo iniciar INET IVS");
}

#[cfg(test)]
mod pruebas {
    use super::origen_permitido;

    #[test]
    fn acepta_los_origenes_de_la_aplicacion() {
        for url in [
            "https://inet-ivs.inversierra.cl/",
            "https://inet-ivs.inversierra.cl/pedidos/",
            "http://127.0.0.1:4321/",
            "http://localhost:4321/pedidos/",
            "tauri://localhost/",
        ] {
            assert!(origen_permitido(&url.parse().unwrap()), "{url}");
        }
    }

    #[test]
    fn rechaza_los_origenes_no_autorizados() {
        for url in [
            "https://otro.example/",
            "http://inet-ivs.inversierra.cl/",
            "https://inet-ivs.inversierra.cl.otro.example/",
            "https://otro.example/#https://inet-ivs.inversierra.cl",
            "http://127.0.0.1:4322/",
        ] {
            assert!(!origen_permitido(&url.parse().unwrap()), "{url}");
        }
    }
}
