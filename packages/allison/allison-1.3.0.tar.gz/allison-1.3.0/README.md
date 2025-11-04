

# ⚠️ **Allison → Sorix**

**Allison** ha sido **renombrada oficialmente a [Sorix](https://pypi.org/project/sorix/)**.
Este paquete (`allison`) permanecerá disponible únicamente por compatibilidad, pero **ya no recibirá actualizaciones**.

Sorix continúa el desarrollo de Allison bajo un nuevo nombre, con la misma base NumPy/CuPy y mejoras en rendimiento, documentación y organización interna.

---

## 🚀 **Migración**

Actualice su entorno a **Sorix** ejecutando:

```bash
pip install sorix
```

Y reemplace en su código:

```python
# Antes
from allison import tensor

# Ahora
from sorix import tensor
```

El paquete `allison` seguirá funcionando temporalmente, pero mostrará una advertencia de deprecación.
Para garantizar compatibilidad futura, se recomienda migrar a `sorix` lo antes posible.

---

## 🧠 **Sobre Sorix**

**Sorix** es una librería de aprendizaje automático basada en **NumPy/CuPy**, diseñada para el estudio de los principios fundamentales de frameworks como PyTorch.
Proporciona un sistema de autograd completo, soporte para GPU y una arquitectura modular para experimentación científica y docente.

![Sorix Training Animation](https://storage.googleapis.com/open-projects-data/Allison/training_animation.gif)

---

## 🔧 **Instalación (nuevo paquete)**

Con **pip**:

```bash
pip install sorix
```

Con **Poetry**:

```bash
poetry add sorix
```

Con **UV**:

```bash
uv add sorix
```

---

## ⚡ **Ejemplo rápido**

```python
from sorix import tensor

x = tensor([2.0], requires_grad=True)
w = tensor([3.0], requires_grad=True)
b = tensor([1.0], requires_grad=True)

y = w * x + b
y.backward()

print("dy/dx:", x.grad)
print("dy/dw:", w.grad)
print("dy/db:", b.grad)
```

---

## 📚 **Documentación y ejemplos**

Los ejemplos y notebooks actualizados están disponibles en el nuevo repositorio:

🔗 [Sorix Repository](https://github.com/Mitchell-Mirano/sorix)

Incluye:

* Fundamentos del sistema tensorial
* Ejemplos de autograd
* Entrenamiento de redes neuronales simples
* Uso de GPU con CuPy

---

## 🧩 **Estado del proyecto**

* Allison → **Deprecado** (solo mantenido por compatibilidad)
* Sorix → **Desarrollo activo** ✅

Se recomienda a todos los usuarios migrar a Sorix para acceder a las versiones más recientes, soporte de GPU mejorado y nuevas funciones de autograd.

---

## 📎 **Enlaces**

| Recurso                          | Enlace                                                                           |
| -------------------------------- | -------------------------------------------------------------------------------- |
| 📦 PyPI (Allison, versión final) | [pypi.org/project/allison](https://pypi.org/project/allison/)                    |
| 🧠 PyPI (Nuevo paquete)          | [pypi.org/project/sorix](https://pypi.org/project/sorix/)                        |
