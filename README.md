# GunboundWC S1 Avatar Editor
![Screenshot](https://raw.githubusercontent.com/agasready/GunboundWC_Avatar_Editor/refs/heads/main/Screenshot%202025-08-27%20151609.png)
A desktop tool for editing **GunboundWC S1 avatar DAT files**.  
Built with Python and Tkinter, this editor allows you to open, edit, and save DAT files used by GunboundWC.  
You can modify avatar attributes, batch-edit multiple entries, and export SQL scripts for easy integration with your game server.

## Features
- Open and edit `.dat` files body, head, glass, flag and Ex-item record.
- Modify fields such as:
  - Avatar code, name, image number
  - Shop visibility
  - Gold and Cash prices (weekly, monthly, eternal)
  - Stats (attack, defense, energy, shield regen, item delay, popularity)
- Batch edit selected rows.
- Direct table editing with double-click.
- Export to SQL:
  - `menu` table inserts
  - `item` table inserts
- Built-in checks for invalid values (length limits, numeric-only fields, etc.).

## Requirements
- Python 3.8+
- Tkinter (usually included with Python)
- No external libraries required besides the Python standard library.

## Usage
1. Clone this repository:
   ```bash
   git clone https://github.com/agasready/GunboundWC_Avatar_Editor.git
   cd GunboundWC_Avatar_Editor
