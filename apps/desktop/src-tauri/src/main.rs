#![cfg_attr(
    all(not(debug_assertions), target_os = "windows"),
    windows_subsystem = "windows"
)]

use tauri::{CustomMenuItem, SystemTray, SystemTrayMenu, SystemTrayMenuItem, SystemTrayEvent, Manager, WindowEvent};
use auto_launch::AutoLaunchBuilder;
use std::env;

fn main() {
    // 1. Build the System Tray Menu
    let show = CustomMenuItem::new("show".to_string(), "Show CAT Agent");
    let quit = CustomMenuItem::new("quit".to_string(), "Quit");
    let tray_menu = SystemTrayMenu::new()
        .add_item(show)
        .add_native_item(SystemTrayMenuItem::Separator)
        .add_item(quit);
        
    let system_tray = SystemTray::new().with_menu(tray_menu);

    tauri::Builder::default()
        .setup(|app| {
            // Force enable autostart on Windows registry when the app launches
            let app_name = "CAT Desktop";
            let app_path = env::current_exe().unwrap().to_str().unwrap().to_string();
            
            let auto = AutoLaunchBuilder::new()
                .set_app_name(app_name)
                .set_app_path(&app_path)
                .set_args(&["--hidden"])
                .build()
                .unwrap();
                
            let _ = auto.enable();
            Ok(())
        })
        // 3. Attach the System Tray
        .system_tray(system_tray)
        .on_system_tray_event(|app, event| match event {
            SystemTrayEvent::DoubleClick { .. } => {
                let window = app.get_window("main").unwrap();
                window.show().unwrap();
                window.set_focus().unwrap();
            }
            SystemTrayEvent::MenuItemClick { id, .. } => {
                match id.as_str() {
                    "quit" => {
                        std::process::exit(0);
                    }
                    "show" => {
                        let window = app.get_window("main").unwrap();
                        window.show().unwrap();
                        window.set_focus().unwrap();
                    }
                    _ => {}
                }
            }
            _ => {}
        })
        // 4. Prevent the app from exiting when the window is closed (minimize to tray)
        .on_window_event(|event| match event.event() {
            WindowEvent::CloseRequested { api, .. } => {
                // Prevent the default closing action
                api.prevent_close();
                // Hide the window instead
                event.window().hide().unwrap();
            }
            _ => {}
        })
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
