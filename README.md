# CI/CD Pipeline Python — Respuestas Taller Entregable 2

## 1. ¿Qué ventajas le proporciona a un proyecto el uso de un pipeline de CI? Menciona al menos tres ventajas específicas y explica por qué son importantes.

**Detección temprana de errores:** Cada vez que se hace un push al repositorio, el pipeline se ejecuta de forma automática. Esto quiere decir que se detecta inmediatamente cualquier inconveniente que se introduce en el código, antes de que se sume o impacte otras áreas del proyecto.

**Estándar de calidad objetiva y continua:** Herramientas como Flake8, Pylint y Black comprueban de manera automática el estilo, la complejidad y la aparición de posibles fallos en cada ejecución. SonarCloud se complementa con un análisis constante de bugs, code smells y seguridad. Esto garantiza que todo el código que se introduce en el repositorio siga los mismos estándares, sin necesidad de revisiones manuales.

**Confianza para integrar cambios frecuentemente:** Integrar cambios pequeños con frecuencia, como indica el taller en su explicación del desarrollo basado en tronco (Trunk-Based Development), disminuye los conflictos de fusión y acelera la entrega de valor. El pipeline proporciona evidencia objetiva (pruebas unitarias y de aceptación aprobadas, Quality Gate aprobado) de que las modificaciones recientes no han causado ninguna ruptura con lo ya existente, lo cual disminuye el temor a la integración frecuente.

---

## 2. ¿Cuál es la diferencia principal entre una prueba unitaria y una prueba de aceptación? Da un ejemplo de algo que probarías con una prueba unitaria y algo que probarías con una prueba de aceptación (en el contexto de cualquier aplicación que conozcas, descríbela primero).

Una **prueba unitaria** Comprueba el funcionamiento de una unidad aislada de código (una función, un método o una clase) sin la necesidad de depender de elementos externos. Su finalidad es verificar que esa pieza lógica opera de manera adecuada por sí misma.

Una **prueba de aceptación** Comprueba que el funcionamiento de la aplicación completa es el que un usuario real espera, emulando interacciones por medio de la interfaz (API, UI, etc.). Depende de que el sistema esté funcionando y se estén probando flujos completos de principio a fin.

**Ejemplo concreto con la calculadora del taller:**

- **Prueba unitaria:** Verificar que la función dividir(10, 2) retorna 5.0 y que dividir(1, 0) lanza un ZeroDivisionError. Aquí se prueba la lógica pura sin involucrar Flask ni el navegador.

- **Prueba de aceptación:** Abrir la página de la calculadora en un navegador, escribir 10 y 2 en los campos, seleccionar "Dividir", hacer clic en "Calcular" y verificar que en la página aparezca el texto Resultado: 5.0. Aquí se prueba todo el sistema funcionando junto: el servidor, las rutas Flask, el HTML y el comportamiento del navegador.

---

## 3. Steps principales del workflow de GitHub Actions

**`actions/checkout@v3`** clona el código del repositorio en el runner de GitHub Actions. Sin este paso, todos los demás steps no tendrían acceso al código fuente y no podrían ejecutarse.

**`Set up Python`** instala y configura la versión de Python especificada (3.12) en el entorno del runner. Esto garantiza que el entorno de ejecución del pipeline sea equivalente al entorno de desarrollo local, evitando inconsistencias por diferencias de versión.

**`Install dependencies`** ejecuta `pip install -r requirements.txt` para instalar todas las librerías necesarias del proyecto (Flask, pytest, Selenium, etc.). Es un prerequisito para que cualquier paso posterior pueda ejecutar código Python del proyecto.

**`Run Black`** ejecuta el formateador en modo verificación (`--check`) sobre la carpeta `app`. No modifica archivos, solo comprueba si el código tiene el formato esperado. Si detecta diferencias, el pipeline falla, forzando al equipo a mantener un estilo de código uniforme antes de poder integrar cambios.

**`Run Pylint`** analiza el código en busca de errores, malas prácticas y problemas de calidad, guardando el resultado en `pylint-report.txt`. El `|| true` evita que un hallazgo detenga el pipeline en este punto, permitiendo que los resultados lleguen a SonarCloud para ser consolidados allí.

**`Run Flake8`** complementa a Pylint verificando el cumplimiento del estándar PEP 8 y detectando errores lógicos adicionales. De igual manera genera un archivo `flake8-report.txt` que SonarCloud consumirá posteriormente para tener una visión completa del análisis estático.

**`Run Unit Tests with pytest and Coverage`** ejecuta todas las pruebas unitarias (excluyendo las de aceptación) y genera el archivo `coverage.xml`. Este paso valida que la lógica del negocio funciona correctamente y mide qué porcentaje del código está siendo cubierto por las pruebas. Si alguna prueba falla, el pipeline se detiene aquí.

**`Run Acceptance Tests`** levanta la aplicación con Gunicorn en segundo plano, espera a que esté lista y luego ejecuta las pruebas de Selenium contra ella. Verifica que el sistema completo funciona desde la perspectiva de un usuario real, simulando interacciones en el navegador como llenar formularios y validar resultados en pantalla.

**`Upload Test Reports Artifacts`** sube los reportes HTML generados por pytest como artefactos descargables del workflow. Esto permite revisar el detalle de las pruebas directamente desde la interfaz de GitHub Actions sin necesidad de ejecutar el pipeline localmente.

**`SonarCloud Scan`** envía el código fuente junto con los reportes de Pylint, Flake8 y Coverage a SonarCloud para un análisis centralizado. Aplica el Quality Gate configurado y, si el código no cumple los estándares mínimos definidos (cobertura, bugs, code smells), el pipeline falla en este punto.

**`Set up QEMU`** configura la emulación de arquitecturas en el runner. Esto es necesario para que el paso posterior pueda construir imágenes Docker dirigidas a múltiples plataformas (como `amd64` y `arm64`) desde un único entorno. Solo se ejecuta cuando hay un push directo a `main`.

**`Set up Docker Buildx`** activa el constructor avanzado de Docker, que habilita la construcción multi-plataforma y el uso de caché entre ejecuciones del pipeline para acelerar builds futuros. También se ejecuta únicamente en push a `main`.

**`Login to Docker Hub`** autentica el runner contra Docker Hub usando el nombre de usuario y el token de acceso configurados como variable y secreto respectivamente. Es un prerequisito para poder publicar la imagen en el registro.

**`Build and push Docker image`** construye la imagen Docker a partir del `Dockerfile` del proyecto y la publica en Docker Hub con dos etiquetas: el SHA del commit para trazabilidad exacta, y `latest` para facilitar el acceso a la versión más reciente. Usa caché para reducir los tiempos de construcción en ejecuciones posteriores. Este es el paso final que convierte el código validado en un artefacto desplegable y listo para producción.

---

## 4. ¿Qué problemas o dificultades encontraste al implementar este taller?

Entender cómo se coordinan las pruebas de aceptación y el servidor de la aplicación en un mismo trabajo de GitHub Actions fue lo más fascinante del taller. Poner Gunicorn en segundo plano usando & y añadir un sleep 10 para esperar que el servidor esté listo antes de lanzar Selenium no fue una solución que se percibiera inmediatamente. Si el tiempo de espera es insuficiente, los ensayos no tienen éxito debido a errores de conexión que pueden confundirse con fallos en el test mismo.

Otra enseñanza importante fue la distinción entre secretos y variables en GitHub Actions. Por precaución, tenemos la tendencia de mantener todo en secreto; sin embargo, el taller deja claro que valores como SONAR_HOST_URL o DOCKERHUB_USERNAME son configuraciones y no credenciales. Al manejarlos como variables, el pipeline se vuelve más transparente y fácil de depurar sin poner en riesgo la seguridad.

Finalmente, entender el orden de las capas en el Dockerfile fue valioso: copiar primero requirements.txt e instalar dependencias antes de copiar el resto del código permite que Docker reutilice esa capa de caché en builds posteriores cuando las dependencias no cambiaron, acelerando considerablemente las construcciones.

Pero como tal una de las principales dificulatades que tuvimos es que alprincipio cada vez que corregiamos un error de sonar y le haciamos push nos fallaba el black -check por no correr el black desde antes en el codigo antes de subirlo asi que apartir de eso siempre corriamos el black antes de hacer push.

---

## 5. ¿Qué ventajas ofrece empaquetar la aplicación en una imagen Docker al final del pipeline?

El taller señala que simplemente validar el código no es suficiente para garantizar despliegues consistentes. Empaquetar en Docker al final del pipeline ofrece ventajas concretas:

**Entorno reproducible en cualquier lugar:** La imagen contiene el código, la versión de Python, las dependencias y la configuración de Gunicorn. Esto soluciona inconvenientes de compatibilidad entre entornos: la misma imagen es efectiva en desarrollo, staging y producción.

**Trazabilidad por commit:** El canal de procesamiento asigna dos etiquetas a la imagen: `latest` y el SHA del commit que la generó. Esto posibilita que en cualquier momento se pueda conocer cuál versión del código está funcionando en producción y, si fuese requerido, revertir a una imagen previa.

**Preparación para despliegues modernos:** Este enfoque _"nos capacita para prácticas modernas de despliegue"_ como indica el taller. La aplicación puede ser ejecutada en cualquier entorno con Docker sin requerir la configuración de Python ni la instalación manual de dependencias, lo que permite una integración más sencilla con orquestadores y procesos de entrega continua.