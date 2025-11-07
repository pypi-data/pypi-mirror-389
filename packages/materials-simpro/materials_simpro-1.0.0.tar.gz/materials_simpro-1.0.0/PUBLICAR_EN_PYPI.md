# Guía Rápida: Publicar Materials-SimPro en PyPI

## ✅ Pre-requisitos (LISTOS)

- [x] `pyproject.toml` creado
- [x] `MANIFEST.in` creado
- [x] `setup.py` con post-install hooks
- [x] `README.md` documentado
- [x] Código en GitHub

## 📦 Pasos para Publicar

### 1. Crear Cuenta en PyPI

```bash
# Registrarse en:
https://pypi.org/account/register/

# Y en TestPyPI (para pruebas):
https://test.pypi.org/account/register/
```

### 2. Instalar Herramientas

```bash
pip install --upgrade build twine
```

### 3. Construir el Paquete

```bash
cd G:\Materials-SimPro

# Limpiar builds anteriores
rm -rf dist/ build/ *.egg-info

# Construir
python -m build
```

Esto crea:
- `dist/materials-simpro-1.0.0.tar.gz` (~50 MB)
- `dist/materials_simpro-1.0.0-py3-none-any.whl` (~50 MB)

### 4. Probar en TestPyPI (Recomendado)

```bash
# Upload a Test PyPI
twine upload --repository testpypi dist/*

# Probar instalación
pip install --index-url https://test.pypi.org/simple/ materials-simpro
```

### 5. Publicar en PyPI Real

```bash
# Upload a PyPI
twine upload dist/*

# Ingresa tu API token cuando lo pida
```

### 6. Verificar

```bash
# Instalar desde PyPI
pip install materials-simpro

# Probar
python -c "import materials_simpro; print('OK')"
```

## 🔐 API Token (Recomendado)

En lugar de password, usa API token:

1. Ve a https://pypi.org/manage/account/token/
2. Crea token con scope "Entire account"
3. Guarda en `~/.pypirc`:

```ini
[pypi]
username = __token__
password = pypi-AgEIcHlwaS5vcmcC...

[testpypi]
username = __token__
password = pypi-AgENdGVzdC5weXBpLm9yZwI...
```

## 🚀 Comandos Completos

```bash
# Build
python -m build

# Test
twine upload -r testpypi dist/*
pip install -i https://test.pypi.org/simple/ materials-simpro

# Producción
twine upload dist/*

# Verificar
pip install materials-simpro
```

## 📝 Actualizar Versión

Para nueva versión:

1. Edita `pyproject.toml`: `version = "1.0.1"`
2. Edita `setup.py`: `version="1.0.1-alpha"`
3. `git tag v1.0.1`
4. `python -m build`
5. `twine upload dist/*`

---

**¡Listo! En 10 minutos el paquete estará en PyPI** 🚀

```bash
pip install materials-simpro
```
