import os
import re

def fix_colors_in_file(filepath):
    """Corrige el uso de ft.Colors a ft.colors (Flet 0.24.1 compatibility)"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Reemplazar ft.Colors por ft.colors
        original = content
        content = re.sub(r'ft\.colors\.', 'ft.colors.', content)
        
        if content != original:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✅ Corregido: {filepath}")
            return True
        else:
            print(f"⏭️ Sin cambios: {filepath}")
            return False
    except Exception as e:
        print(f"❌ Error en {filepath}: {e}")
        return False

def fix_all_python_files():
    """Corrige todos los archivos Python del proyecto"""
    corrected = 0
    
    # Módulos a revisar
    modules = [
        'main.py',
        'modules/auth.py',
        'modules/dashboard.py',
        'modules/database_manager.py',
        'modules/migrations.py',
        'modules/usuarios.py',
        'modules/ventas.py',
        'modules/pedidos.py',
        'modules/productos.py',
        'modules/clientes.py',
    ]
    
    for module in modules:
        if os.path.exists(module):
            if fix_colors_in_file(module):
                corrected += 1
    
    print(f"\n🎉 Total de archivos corregidos: {corrected}")

if __name__ == "__main__":
    fix_all_python_files()
