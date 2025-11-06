"""
Arquivo com interface gráfica para atualizar branch, gerar build e publicar no PyPI
"""
import os
import re
import subprocess
import sys
import tkinter as tk
from tkinter import messagebox, simpledialog
from pathlib import Path


def get_version():
    """Obtém a versão do arquivo __init__.py"""
    version_file = os.path.join("src", "__init__.py")
    if not os.path.exists(version_file):
        # Tenta no diretório pai
        version_file = os.path.join("..", "src", "__init__.py")
    
    with open(version_file, "r", encoding="utf-8") as f:
        content = f.read()
    match = re.search(r'__version__\s*=\s*[\'"]([^\'"]+)[\'"]', content)
    if match:
        return match.group(1)
    raise RuntimeError("Não foi possível encontrar a variável __version__.")


def incrementar_versao(versao_atual):
    """Incrementa a versão no último número (patch version)"""
    # Divide a versão em partes
    partes = versao_atual.split('.')
    
    # Se não conseguir dividir, retorna None
    if len(partes) < 1:
        return None
    
    # Converte a última parte para inteiro e incrementa
    try:
        ultima_parte = int(partes[-1])
        partes[-1] = str(ultima_parte + 1)
        return '.'.join(partes)
    except ValueError:
        # Se a última parte não for um número, tenta incrementar como string
        return None


def atualizar_branch():
    """Atualiza a branch executando os comandos git especificados e incrementa a versão automaticamente"""
    try:
        # Determina o diretório do repositório git
        original_dir = os.getcwd()
        version_file = os.path.join("src", "__init__.py")
        if not os.path.exists(version_file):
            version_file = os.path.join("..", "src", "__init__.py")
            if not os.path.exists(version_file):
                messagebox.showerror("Erro", "Arquivo src/__init__.py não encontrado!")
                return False
        
        # Se o arquivo está no diretório pai, o repositório está lá
        if version_file.startswith(".."):
            repo_dir = os.path.join(original_dir, "..")
            repo_dir = os.path.abspath(repo_dir)
        else:
            repo_dir = original_dir
        
        # Executa os comandos git no diretório do repositório
        os.chdir(repo_dir)
        
        try:
            # Primeiro, atualiza a branch normalmente
            commands = [
                ["git", "checkout", "develop"],
                ["git", "pull"],
                ["git", "checkout", "main"],
                ["git", "merge", "develop"],
                ["git", "push", "origin", "main"]
            ]
            
            for cmd in commands:
                result = subprocess.run(cmd, capture_output=True, text=True, check=True)
                print(f"✓ {' '.join(cmd)} executado com sucesso")
                if result.stdout:
                    print(result.stdout)
            
            # Após atualizar a branch, obtém a versão atual e incrementa
            # Usa o caminho relativo ao diretório do repositório
            git_path = "src/__init__.py"
            versao_atual = get_version()
            nova_versao = incrementar_versao(versao_atual)
            
            if not nova_versao:
                messagebox.showerror("Erro", f"Não foi possível incrementar a versão: {versao_atual}")
                return False
            
            # Atualiza o arquivo __init__.py com a nova versão
            with open(git_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            # Substitui a versão
            new_content = re.sub(
                r'__version__\s*=\s*[\'"]([^\'"]+)[\'"]',
                f'__version__ = \'{nova_versao}\'',
                content
            )
            
            # Salva o arquivo
            with open(git_path, "w", encoding="utf-8") as f:
                f.write(new_content)
            
            # Faz commit e push da nova versão
            version_commands = [
                ["git", "add", git_path],
                ["git", "commit", "-m", f"Atualiza versão para {nova_versao}"],
                ["git", "push", "origin", "main"]
            ]
            
            for cmd in version_commands:
                result = subprocess.run(cmd, capture_output=True, text=True, check=True)
                print(f"✓ {' '.join(cmd)} executado com sucesso")
                if result.stdout:
                    print(result.stdout)
                    
        finally:
            os.chdir(original_dir)
        
        messagebox.showinfo("Sucesso", f"Branch atualizada com sucesso!\nVersão atualizada automaticamente de {versao_atual} para {nova_versao}")
        return True
    except subprocess.CalledProcessError as e:
        error_msg = f"Erro ao executar comando:\n{e}\n\nStderr: {e.stderr}"
        messagebox.showerror("Erro", error_msg)
        return False
    except Exception as e:
        error_msg = f"Erro inesperado: {str(e)}"
        messagebox.showerror("Erro", error_msg)
        return False


def gerar_build():
    """Gera o build executando setup.py"""
    try:
        # Determina o diretório do repositório
        original_dir = os.getcwd()
        setup_file = "setup.py"
        repo_dir = original_dir
        
        if not os.path.exists(setup_file):
            setup_file = "../setup.py"
            if not os.path.exists(setup_file):
                messagebox.showerror("Erro", "Arquivo setup.py não encontrado!")
                return False
            # Se setup.py está no diretório pai, o repositório está lá
            repo_dir = os.path.join(original_dir, "..")
            repo_dir = os.path.abspath(repo_dir)
        
        # Muda para o diretório do repositório
        os.chdir(repo_dir)
        
        try:
            # Limpa builds antigos antes de gerar novos
            import shutil
            dirs_para_limpar = ["build", "dist"]
            for dir_name in dirs_para_limpar:
                if os.path.exists(dir_name):
                    try:
                        shutil.rmtree(dir_name)
                        print(f"✓ Diretório {dir_name} limpo")
                    except Exception as e:
                        print(f"⚠ Aviso: Não foi possível limpar {dir_name}: {e}")
            
            # Limpa arquivos .egg-info
            for item in os.listdir("."):
                if item.endswith(".egg-info") and os.path.isdir(item):
                    try:
                        shutil.rmtree(item)
                        print(f"✓ Diretório {item} limpo")
                    except Exception as e:
                        print(f"⚠ Aviso: Não foi possível limpar {item}: {e}")
            
            # Tenta primeiro usar python -m build (método moderno recomendado)
            # Se não funcionar, usa setup.py como fallback
            try:
                cmd = [sys.executable, "-m", "build"]
                result = subprocess.run(cmd, capture_output=True, text=True, check=True)
                print(result.stdout)
                if result.stderr:
                    print(result.stderr)
                messagebox.showinfo("Sucesso", "Build gerado com sucesso!")
                return True
            except (subprocess.CalledProcessError, FileNotFoundError):
                # Fallback para setup.py se build não estiver disponível
                print("⚠ Usando setup.py como fallback (python -m build não disponível)")
                cmd = [sys.executable, "setup.py", "sdist", "bdist_wheel"]
                result = subprocess.run(cmd, capture_output=True, text=True, check=True)
                print(result.stdout)
                if result.stderr:
                    print(result.stderr)
                messagebox.showinfo("Sucesso", "Build gerado com sucesso!")
                return True
        finally:
            os.chdir(original_dir)
            
    except subprocess.CalledProcessError as e:
        error_details = f"Comando: {' '.join(e.cmd)}\n\n"
        if e.stdout:
            error_details += f"Stdout:\n{e.stdout}\n\n"
        if e.stderr:
            error_details += f"Stderr:\n{e.stderr}"
        else:
            error_details += "Stderr: (vazio)"
        error_msg = f"Erro ao gerar build:\n\n{error_details}"
        messagebox.showerror("Erro", error_msg)
        return False
    except Exception as e:
        error_msg = f"Erro inesperado: {str(e)}"
        messagebox.showerror("Erro", error_msg)
        return False


def publicar_pypi():
    """Publica o pacote no PyPI usando twine"""
    try:
        # Obtém a versão
        nova_versao = get_version()
        
        # Solicita credenciais do usuário
        username = simpledialog.askstring("PyPI Username", "Digite o username do PyPI:", show='*')
        if not username:
            messagebox.showwarning("Cancelado", "Publicação cancelada. Username não informado.")
            return False
        
        password = simpledialog.askstring("PyPI Password", "Digite a senha do PyPI:", show='*')
        if not password:
            messagebox.showwarning("Cancelado", "Publicação cancelada. Senha não informada.")
            return False
        
        # Determina onde está o diretório dist
        original_dir = os.getcwd()
        dist_dir = "dist"
        repo_dir = original_dir
        
        if not os.path.exists(dist_dir):
            dist_dir = "../dist"
            if not os.path.exists(dist_dir):
                messagebox.showerror("Erro", "Diretório dist não encontrado! Execute 'Gerar Build' primeiro.")
                return False
            # Se dist está no diretório pai, o repositório está lá
            repo_dir = os.path.join(original_dir, "..")
            repo_dir = os.path.abspath(repo_dir)
            dist_dir_abs = os.path.abspath(dist_dir)
        else:
            dist_dir_abs = os.path.abspath(dist_dir)
        
        # Nomes dos arquivos
        tar_filename = f"oking-{nova_versao}.tar.gz"
        whl_filename = f"oking-{nova_versao}-py3-none-any.whl"
        
        tar_file = os.path.join(dist_dir_abs, tar_filename)
        whl_file = os.path.join(dist_dir_abs, whl_filename)
        
        # Verifica se os arquivos existem
        if not os.path.exists(tar_file):
            messagebox.showerror("Erro", f"Arquivo não encontrado: {tar_file}\nExecute 'Gerar Build' primeiro.")
            return False
        
        if not os.path.exists(whl_file):
            messagebox.showerror("Erro", f"Arquivo não encontrado: {whl_file}\nExecute 'Gerar Build' primeiro.")
            return False
        
        # Executa o comando twine no diretório do repositório
        os.chdir(repo_dir)
        try:
            # Valida os metadados antes de publicar
            print("Validando metadados dos arquivos...")
            check_cmd = ["twine", "check", tar_file, whl_file]
            check_result = subprocess.run(check_cmd, capture_output=True, text=True)
            
            if check_result.returncode != 0:
                error_msg = f"Erro na validação dos metadados:\n{check_result.stdout}\n{check_result.stderr}\n\n"
                error_msg += "Por favor, execute 'Gerar Build' novamente para regenerar os arquivos com metadados corretos."
                messagebox.showerror("Erro de Validação", error_msg)
                return False
            
            print("✓ Metadados validados com sucesso")
            
            # Usa caminhos absolutos para garantir que funcionem
            cmd = [
                "twine", "upload",
                tar_file,
                whl_file,
                "-u", username,
                "-p", password
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            print(result.stdout)
            if result.stderr:
                print(result.stderr)
            messagebox.showinfo("Sucesso", f"Pacote publicado no PyPI com sucesso!\nVersão: {nova_versao}")
            return True
        finally:
            os.chdir(original_dir)
            
    except subprocess.CalledProcessError as e:
        error_details = f"Comando: {' '.join(e.cmd)}\n\n"
        if e.stdout:
            error_details += f"Stdout:\n{e.stdout}\n\n"
        if e.stderr:
            error_details += f"Stderr:\n{e.stderr}"
        else:
            error_details += "Stderr: (vazio)"
        error_msg = f"Erro ao publicar no PyPI:\n\n{error_details}"
        messagebox.showerror("Erro", error_msg)
        return False
    except FileNotFoundError:
        messagebox.showerror("Erro", "Twine não encontrado! Instale com: pip install twine")
        return False
    except Exception as e:
        error_msg = f"Erro inesperado: {str(e)}"
        messagebox.showerror("Erro", error_msg)
        return False


def criar_interface():
    """Cria a interface gráfica com os 3 botões"""
    root = tk.Tk()
    root.title("Build e Publicação PyPI")
    root.geometry("400x280")
    root.resizable(False, False)
    
    # Frame principal
    frame = tk.Frame(root, padx=20, pady=20)
    frame.pack(fill=tk.BOTH, expand=True)
    
    # Título
    titulo = tk.Label(frame, text="Gerenciamento de Build e Publicação", 
                     font=("Arial", 14, "bold"))
    titulo.pack(pady=(0, 15))
    
    # Botão 1: Atualizar Branch
    btn_atualizar = tk.Button(
        frame,
        text="Atualizar Branch",
        command=atualizar_branch,
        width=25,
        height=2,
        bg="#4CAF50",
        fg="white",
        font=("Arial", 10, "bold"),
        cursor="hand2"
    )
    btn_atualizar.pack(pady=8)
    
    # Botão 2: Gerar Build
    btn_build = tk.Button(
        frame,
        text="Gerar Build",
        command=gerar_build,
        width=25,
        height=2,
        bg="#2196F3",
        fg="white",
        font=("Arial", 10, "bold"),
        cursor="hand2"
    )
    btn_build.pack(pady=8)
    
    # Botão 3: Publicar no PyPI
    btn_pypi = tk.Button(
        frame,
        text="Publicar no PyPI",
        command=publicar_pypi,
        width=25,
        height=2,
        bg="#FF9800",
        fg="white",
        font=("Arial", 10, "bold"),
        cursor="hand2"
    )
    btn_pypi.pack(pady=8)
    
    # Centraliza a janela
    root.update_idletasks()
    width = root.winfo_width()
    height = root.winfo_height()
    x = (root.winfo_screenwidth() // 2) - (width // 2)
    y = (root.winfo_screenheight() // 2) - (height // 2)
    root.geometry(f'{width}x{height}+{x}+{y}')
    
    root.mainloop()


if __name__ == "__main__":
    criar_interface()
