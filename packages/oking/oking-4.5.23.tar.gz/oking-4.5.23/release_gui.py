"""
OKING Hub - Release GUI

Recria o fluxo do release.ps1 com interface gráfica em Python (Tkinter):
- Ler versão atual de src/__init__.py
- Selecionar incremento (major/minor/patch)
- Salvar nova versão
- Limpar builds anteriores (dist, build, oking.egg-info)
- Gerar wheel (setup.py sdist bdist_wheel)
- Upload para PyPI (python -m twine upload)

Execução:
  venv\\Scripts\\python.exe release_gui.py
  (ou python release_gui.py)
"""

from __future__ import annotations

import os
import re
import sys
import subprocess
import shutil
from pathlib import Path
import threading
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog


# ----------------------- Utilidades de log (thread-safe) -----------------------
class Logger:
    def __init__(self, text_widget: tk.Text) -> None:
        self._text = text_widget
        self._lock = threading.Lock()

    def _append(self, msg: str) -> None:
        self._text.configure(state=tk.NORMAL)
        self._text.insert(tk.END, msg)
        self._text.see(tk.END)
        self._text.configure(state=tk.DISABLED)

    def info(self, msg: str) -> None:
        with self._lock:
            self._append(f"[INFO] {msg}\n")

    def ok(self, msg: str) -> None:
        with self._lock:
            self._append(f"[OK] {msg}\n")

    def warn(self, msg: str) -> None:
        with self._lock:
            self._append(f"[WARN] {msg}\n")

    def error(self, msg: str) -> None:
        with self._lock:
            self._append(f"[ERROR] {msg}\n")

    def step(self, title: str) -> None:
        with self._lock:
            self._append("\n===================================================\n")
            self._append(f"  {title}\n")
            self._append("===================================================\n\n")


# ----------------------------- Lógica de domínio ------------------------------
INIT_FILE = Path("src/__init__.py")


def detect_python_executable() -> str:
    venv_python = Path("venv/Scripts/python.exe") if os.name == "nt" else Path("venv/bin/python")
    if venv_python.exists():
        return str(venv_python)
    return sys.executable or "python"


def read_current_version(log: Logger) -> str | None:
    log.step("ETAPA 1: Lendo versão atual")
    if not INIT_FILE.exists():
        log.error(f"Arquivo {INIT_FILE.as_posix()} não encontrado!")
        return None
    content = INIT_FILE.read_text(encoding="utf-8")
    m = re.search(r"__version__\s*=\s*'(\d+)\.(\d+)\.(\d+)'", content)
    if not m:
        log.error(f"Não foi possível extrair a versão de {INIT_FILE.as_posix()}")
        return None
    current = f"{int(m.group(1))}.{int(m.group(2))}.{int(m.group(3))}"
    log.info(f"Versão atual: {current}")
    return current


def compute_new_version(current_version: str, inc: str) -> str:
    m = re.match(r"^(\d+)\.(\d+)\.(\d+)$", current_version)
    if not m:
        raise ValueError("Versão atual inválida")
    maj, min_, pat = map(int, m.groups())
    if inc == "major":
        maj, min_, pat = maj + 1, 0, 0
    elif inc == "minor":
        min_, pat = min_ + 1, 0
    else:
        pat = pat + 1
    return f"{maj}.{min_}.{pat}"


def save_new_version(log: Logger, old_version: str, new_version: str) -> bool:
    log.step(f"ETAPA 2: Incrementando versão ({old_version} → {new_version})")
    content = INIT_FILE.read_text(encoding="utf-8")
    updated = re.sub(
        rf"__version__\s*=\s*'{re.escape(old_version)}'",
        f"__version__ = '{new_version}'",
        content,
    )
    INIT_FILE.write_text(updated, encoding="utf-8")
    log.ok(f"Versão atualizada de {old_version} → {new_version}")
    return True


def clean_previous_builds(log: Logger) -> None:
    log.step("ETAPA 3: Limpando builds anteriores")
    for folder in ("dist", "build", "oking.egg-info"):
        p = Path(folder)
        if p.exists():
            log.info(f"Removendo diretório {folder}...")
            shutil.rmtree(p, ignore_errors=True)
    log.ok("Limpeza concluída")


def run_command(log: Logger, cmd: list[str]) -> int:
    log.info("Executando: " + " ".join(cmd))
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    assert proc.stdout is not None
    for line in proc.stdout:
        log.info(line.rstrip())
    proc.wait()
    return proc.returncode


def generate_wheel(log: Logger, python_exe: str, version: str) -> tuple[bool, Path | None, Path | None]:
    log.step("ETAPA 4: Gerando wheel (setup.py sdist bdist_wheel)")
    code = run_command(log, [python_exe, "setup.py", "sdist", "bdist_wheel"])
    if code != 0:
        log.error("Falha ao gerar wheel!")
        return False, None, None
    log.ok("Wheel gerada com sucesso!")
    tar_gz = Path("dist") / f"oking-{version}.tar.gz"
    whl = Path("dist") / f"oking-{version}-py3-none-any.whl"
    if not tar_gz.exists():
        log.error(f"Arquivo não encontrado: {tar_gz}")
        return False, None, None
    if not whl.exists():
        log.error(f"Arquivo não encontrado: {whl}")
        return False, None, None
    log.info("Arquivos gerados:")
    log.info(f"  - {tar_gz}")
    log.info(f"  - {whl}")
    return True, tar_gz, whl


def ensure_twine_installed(log: Logger, python_exe: str) -> bool:
    """Verifica se o twine está instalado; se não estiver, pergunta e instala."""
    # Verifica
    code = subprocess.call([python_exe, "-m", "pip", "show", "twine"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if code == 0:
        return True
    # Pergunta para instalar
    try:
        if not messagebox.askyesno("Dependência ausente", "Twine não está instalado no ambiente atual.\nDeseja instalar agora?\n\nComando: python -m pip install --upgrade pip setuptools wheel twine"):
            log.warn("Twine não instalado. Upload não poderá ser executado.")
            return False
    except Exception:
        # Em ambientes sem UI, segue com instalação
        pass
    log.step("Instalando dependências (pip, setuptools, wheel, twine)")
    install_cmd = [python_exe, "-m", "pip", "install", "--upgrade", "pip", "setuptools", "wheel", "twine"]
    rc = run_command(log, install_cmd)
    if rc != 0:
        log.error("Falha ao instalar twine. Instale manualmente: python -m pip install twine")
        return False
    return True


def upload_pypi(log: Logger, python_exe: str, tar_gz: Path, whl: Path, token: str) -> bool:
    log.step("ETAPA 6: Upload para PyPI (twine upload)")
    if not ensure_twine_installed(log, python_exe):
        return False
    # Usa autenticação não interativa: usuário __token__ e password = token
    cmd = [
        python_exe,
        "-m",
        "twine",
        "upload",
        "--non-interactive",
        "--username",
        "__token__",
        "--password",
        token,
        str(tar_gz),
        str(whl),
    ]
    code = run_command(log, cmd)
    if code != 0:
        log.error("Falha no upload!")
        log.warn("A versão foi atualizada mas o upload falhou")
        log.info("Para tentar novamente, execute:")
        log.info(f"  twine upload {tar_gz} {whl}")
        return False
    log.ok("Upload concluído!")
    return True


def run_git_merge_develop_into_main(log: Logger) -> bool:
    """Executa a sequência de git solicitada."""
    log.step("GIT: Atualizando main a partir de develop")
    # Verifica se git está disponível
    try:
        rc = subprocess.call(["git", "--version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except FileNotFoundError:
        rc = 1
    if rc != 0:
        log.error("Git não encontrado no PATH. Instale o Git e tente novamente.")
        return False

    commands: list[list[str]] = [
        ["git", "checkout", "develop"],
        ["git", "pull"],
        ["git", "checkout", "main"],
        ["git", "merge", "develop"],
        ["git", "push", "origin", "main"],
    ]

    for cmd in commands:
        code = run_command(log, cmd)
        if code != 0:
            log.error(f"Comando falhou: {' '.join(cmd)}")
            return False
    log.ok("Branch main atualizado com sucesso.")
    return True


# ---------------------------------- GUI --------------------------------------
class ReleaseApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("OKING Hub - Release")
        self.root.geometry("900x650")

        self.python_exe = detect_python_executable()
        self.increment_type = tk.StringVar(value="patch")
        self.current_version_var = tk.StringVar(value="-")
        self.new_version_var = tk.StringVar(value="-")
        self._pypi_token: str | None = None

        self._build_ui()
        self._logger = Logger(self.txt_log)

        # Inicialização inicial
        self._update_current_version()
        self._compute_new_version()

    # UI setup
    def _build_ui(self) -> None:
        top = ttk.Frame(self.root)
        top.pack(fill=tk.X, padx=16, pady=12)

        ttk.Label(top, text="Versão atual:").grid(row=0, column=0, sticky=tk.W)
        ttk.Label(top, textvariable=self.current_version_var).grid(row=0, column=1, sticky=tk.W, padx=(8, 16))
        ttk.Label(top, text="Nova versão:").grid(row=1, column=0, sticky=tk.W)
        ttk.Label(top, textvariable=self.new_version_var).grid(row=1, column=1, sticky=tk.W, padx=(8, 16))

        grp = ttk.LabelFrame(top, text="Tipo de incremento")
        grp.grid(row=0, column=2, rowspan=2, padx=10)
        for i, label in enumerate(["major", "minor", "patch"]):
            ttk.Radiobutton(grp, text=label, value=label, variable=self.increment_type, command=self._compute_new_version).grid(row=0, column=i, padx=6, pady=6)

        # Buttons row 1
        btn_row1 = ttk.Frame(self.root)
        btn_row1.pack(fill=tk.X, padx=16, pady=(0, 8))
        ttk.Button(btn_row1, text="Ler versão", command=self._update_current_version).pack(side=tk.LEFT)
        ttk.Button(btn_row1, text="Calcular nova", command=self._compute_new_version).pack(side=tk.LEFT, padx=8)
        ttk.Button(btn_row1, text="Salvar versão", command=self._save_version).pack(side=tk.LEFT)
        ttk.Button(btn_row1, text="Executar TUDO", command=self._run_all).pack(side=tk.RIGHT)

        # Buttons row 2
        btn_row2 = ttk.Frame(self.root)
        btn_row2.pack(fill=tk.X, padx=16, pady=(0, 8))
        ttk.Button(btn_row2, text="Limpar builds", command=self._clean).pack(side=tk.LEFT)
        ttk.Button(btn_row2, text="Gerar wheel", command=self._build).pack(side=tk.LEFT, padx=8)
        ttk.Button(btn_row2, text="Upload PyPI", command=self._upload).pack(side=tk.LEFT)

        # Buttons row 3 (Git)
        btn_row3 = ttk.Frame(self.root)
        btn_row3.pack(fill=tk.X, padx=16, pady=(0, 8))
        ttk.Button(btn_row3, text="Git: merge develop → main", command=self._git_merge).pack(side=tk.LEFT)

        # Log
        log_frame = ttk.Frame(self.root)
        log_frame.pack(fill=tk.BOTH, expand=True, padx=16, pady=8)
        self.txt_log = tk.Text(log_frame, wrap=tk.NONE, height=24, state=tk.DISABLED, font=("Consolas", 10))
        self.txt_log.pack(fill=tk.BOTH, expand=True)

    # Helpers
    def _ask_token(self) -> str | None:
        if self._pypi_token:
            return self._pypi_token
        token = simpledialog.askstring(
            "Token PyPI",
            "Informe o token do PyPI (começa com pypi-...):",
            show='*',
            parent=self.root,
        )
        if token:
            self._pypi_token = token.strip()
        return self._pypi_token

    def _update_current_version(self) -> None:
        def task():
            v = read_current_version(self._logger)
            if v:
                self.current_version_var.set(v)
        threading.Thread(target=task, daemon=True).start()

    def _compute_new_version(self) -> None:
        cur = self.current_version_var.get()
        if cur and cur != "-":
            try:
                self.new_version_var.set(compute_new_version(cur, self.increment_type.get()))
            except Exception:
                self.new_version_var.set("-")

    def _save_version(self) -> None:
        cur = self.current_version_var.get()
        new = self.new_version_var.get()
        if cur in ("-", "") or new in ("-", ""):
            messagebox.showwarning("Atenção", "Versões inválidas para salvar.")
            return
        def task():
            if save_new_version(self._logger, cur, new):
                self.current_version_var.set(new)
        threading.Thread(target=task, daemon=True).start()

    def _clean(self) -> None:
        threading.Thread(target=lambda: clean_previous_builds(self._logger), daemon=True).start()

    def _build(self) -> None:
        def task():
            version = self.current_version_var.get()
            if version in ("-", ""):
                self._logger.warn("Versão atual desconhecida. Leia/Salve a versão primeiro.")
                return
            ok, tar_gz, whl = generate_wheel(self._logger, self.python_exe, version)
            if ok:
                self._last_artifacts = (tar_gz, whl)
        threading.Thread(target=task, daemon=True).start()

    def _upload(self) -> None:
        token = self._ask_token()
        if not token:
            self._logger.warn("Upload cancelado: token não informado.")
            return
        def task(token_val: str):
            version = self.current_version_var.get()
            if version in ("-", ""):
                self._logger.warn("Versão atual desconhecida. Leia/Salve a versão primeiro.")
                return
            tar_gz = Path("dist") / f"oking-{version}.tar.gz"
            whl = Path("dist") / f"oking-{version}-py3-none-any.whl"
            if not tar_gz.exists() or not whl.exists():
                self._logger.error("Artefatos não encontrados em dist/. Gere a wheel primeiro.")
                return
            if upload_pypi(self._logger, self.python_exe, tar_gz, whl, token_val):
                self._logger.info(f"Versão publicada: {version}")
                self._logger.info(f"PyPI: https://pypi.org/project/oking/{version}/")
        threading.Thread(target=lambda: task(token), daemon=True).start()

    def _run_all(self) -> None:
        token = self._ask_token()
        if not token:
            self._logger.warn("Upload não será realizado: token não informado.")
        def task(token_val: str | None):
            # Ler atual
            v = read_current_version(self._logger)
            if not v:
                return
            self.current_version_var.set(v)
            # Calcular & salvar
            new_v = compute_new_version(v, self.increment_type.get())
            if not save_new_version(self._logger, v, new_v):
                return
            self.current_version_var.set(new_v)
            self.new_version_var.set(new_v)
            # Limpar
            clean_previous_builds(self._logger)
            # Build
            ok, tar_gz, whl = generate_wheel(self._logger, self.python_exe, new_v)
            if not ok:
                return
            # Upload (confirmação via diálogo)
            if token_val and messagebox.askyesno("Confirmação", "Deseja fazer upload para o PyPI?"):
                upload_pypi(self._logger, self.python_exe, tar_gz, whl, token_val)
            self._logger.ok("Processo concluído.")
        threading.Thread(target=lambda: task(token), daemon=True).start()

    def _git_merge(self) -> None:
        if not messagebox.askyesno(
            "Confirmar",
            "Executar sequência:\n\n"
            "git checkout develop\n"
            "git pull\n"
            "git checkout main\n"
            "git merge develop\n"
            "git push origin main\n\n"
            "Deseja continuar?",
        ):
            return
        threading.Thread(target=lambda: run_git_merge_develop_into_main(self._logger), daemon=True).start()


def main() -> int:
    root = tk.Tk()
    ReleaseApp(root)
    root.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


