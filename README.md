# CI/CD Pipeline Python — Respuestas Taller Entregable 3

## URLs de Despliegue

| Ambiente | URL |
|----------|-----|
| **Staging** | http://calculadora-staging-alb-485371350.us-east-1.elb.amazonaws.com/ |
| **Producción** | http://calculadora-production-alb-1726601312.us-east-1.elb.amazonaws.com/ |

---

## 1. Flujo de trabajo completo con Terraform

El pipeline se dispara con cada `push` a `main` y sigue esta secuencia de jobs encadenados:

### commit → CI (`build-test-publish`)
El código recién pusheado pasa por formateo con Black, análisis estático con Pylint y Flake8, pruebas unitarias con pytest y cobertura, y análisis de calidad con SonarCloud. Si todo pasa, se construye una **imagen Docker** etiquetada con el SHA exacto del commit y se publica en Docker Hub. Este SHA es el **artefacto que viaja** por todo el resto del pipeline, garantizando que staging y producción ejecuten exactamente el mismo código que fue probado.

### → Deploy TF Staging (`deploy-tf-staging`)
Terraform inicializa su backend remoto en S3 (estado en `staging/terraform.tfstate`) y aplica los recursos de AWS para staging: ECS Fargate cluster, Application Load Balancer, Security Groups, Target Group con health check en `/health`, Task Definition apuntando a la imagen con el SHA del commit, y el ECS Service. La URL del ALB resultante se captura como output para los jobs siguientes.

### → Update Service Staging (`update-service-staging`)
Ejecuta `aws ecs update-service --force-new-deployment` para que ECS reemplace las tareas en ejecución por la nueva imagen, y espera con `aws ecs wait services-stable` hasta que el servicio esté completamente estable antes de continuar.

### → Test Staging (`test-staging`)
Ejecuta las **pruebas de aceptación** con Selenium contra la URL del ALB de staging. Valida 8 escenarios completos de la calculadora: suma, resta, multiplicación, división, división por cero, entradas inválidas, potencia y módulo. Estas pruebas validan que la aplicación funciona correctamente de punta a punta, interactuando con la interfaz web real como lo haría un usuario.

### → Deploy TF Prod (`deploy-tf-prod`)
Idéntico al deploy de staging, pero Terraform inicializa con estado en `production/terraform.tfstate` y crea recursos nombrados `calculadora-production-*`. La misma imagen Docker con el mismo SHA se despliega ahora en producción. El pipeline solo llega aquí si las pruebas de staging pasaron.

### → Update Service Prod (`update-service-prod`)
Igual que en staging: fuerza nuevo despliegue en el ECS de producción y espera estabilización.

### → Smoke Test Prod (`smoke-test-production`)
Ejecuta un **smoke test mínimo** contra la URL del ALB de producción: verifica que la página carga, que el título contiene "Calculadora" y que el H1 dice exactamente "Calculadora". No hace operaciones completas, solo confirma que el servicio está vivo y respondiendo correctamente.

---

## 2. Terraform e Infraestructura como Código vs. Despliegue Manual

### Ventajas de usar Terraform/IaC

**Reproducibilidad total:** La infraestructura de staging y producción se crean con exactamente el mismo código HCL, simplemente variando `environment_name`. Eso elimina el clásico problema de "funciona en staging pero no en producción" causado por diferencias en la configuración de los entornos.

**Historial y revisabilidad:** Al estar en el repositorio, cualquier cambio en infraestructura pasa por el mismo proceso de revisión que el código de la aplicación. Se puede ver exactamente qué cambió, cuándo y por qué, algo imposible con clics manuales en la consola de AWS.

**Idempotencia:** `terraform apply` puede ejecutarse múltiples veces sin consecuencias negativas. Si el recurso ya existe y no cambió, Terraform no hace nada. Esto hace que el pipeline sea seguro de re-ejecutar.

**Automatización completa:** Sin IaC, alguien tendría que crear manualmente el ALB, el Target Group, los Security Groups, el Cluster, la Task Definition y el Service en cada despliegue o ante cualquier cambio. Con Terraform, el pipeline lo hace solo.

### Desventajas

**Curva de aprendizaje inicial:** Entender el ciclo plan/apply, el manejo del estado remoto en S3, los outputs y las variables de Terraform requiere tiempo. Al principio, errores como el formato de `subnet_ids` (que debía ser una lista HCL, no una cadena separada por comas) no son intuitivos.

**Estado compartido como punto frágil:** El archivo `terraform.tfstate` en S3 es la fuente de verdad de Terraform. Si se corrompe o se borra, Terraform pierde el rastro de los recursos existentes, lo que puede resultar en intentar crear duplicados o no poder destruir recursos. Requiere cuidado adicional.

**Tiempos de ejecución:** Cada `terraform apply` tarda varios minutos mientras AWS aprovisiona los recursos. En el despliegue manual uno podría reutilizar recursos existentes de formas más rápidas (aunque menos reproducibles).

### Experiencia con HCL

Definir la infraestructura en HCL resultó bastante legible una vez superada la sintaxis inicial. La capacidad de referenciar recursos entre sí (por ejemplo, `aws_security_group.alb_sg.id` dentro del recurso del ALB) hace que las dependencias sean explícitas y claras. Lo más valioso fue ver cómo el mismo archivo `main.tf` servía para crear ambos entornos con solo cambiar variables, algo que en la consola de AWS habría requerido repetir cada paso manualmente.

---

## 3. Ventajas y desventajas de introducir un entorno de Staging

### Ventajas

**Barrera de seguridad real:** Los errores que escapan a las pruebas unitarias —problemas de configuración, incompatibilidades con AWS, fallos de red, errores en variables de entorno— se detectan en staging antes de llegar a producción. En este pipeline, si la aplicación no responde al health check del ALB en staging, el deploy de producción nunca ocurre.

**Validación en entorno idéntico al productivo:** Las pruebas de aceptación se ejecutan contra infraestructura AWS real (ECS Fargate + ALB), no contra un servidor local. Esto verifica que la imagen Docker funciona correctamente en el entorno donde realmente va a vivir.

**Confianza para desplegar frecuentemente:** Saber que cada push a main pasa por staging antes de llegar a producción reduce el miedo a desplegar. El equipo puede iterar con más velocidad porque tiene una red de seguridad real.

### Desventajas

**Tiempo total del pipeline:** Añadir staging duplica prácticamente el tiempo de despliegue. Cada entorno requiere `terraform apply` (varios minutos), esperar que ECS estabilice el servicio, y ejecutar las pruebas. El pipeline completo puede tardar 15–25 minutos desde el commit hasta que la imagen está en producción.

**Costo de infraestructura adicional:** Tener staging activo permanentemente implica pagar por un segundo ALB, cluster ECS, tareas Fargate y el tráfico de red, aunque el ambiente no tenga carga real. En proyectos pequeños o de bajo presupuesto, esto puede ser relevante.

**Complejidad de mantenimiento:** Dos entornos significan dos estados de Terraform, dos conjuntos de recursos AWS, dos URLs para gestionar. Si staging queda desincronizado con producción (por ejemplo, con una configuración manual que alguien hizo directamente en AWS), pierde su valor como entorno de prueba fiel.

### Impacto velocidad vs. seguridad

Staging sacrifica velocidad inmediata (el feedback tarda más en llegar) pero aumenta drásticamente la seguridad del despliegue. El balance es favorable en cualquier aplicación que tenga usuarios reales: un bug en producción tiene un costo mucho mayor que esperar unos minutos adicionales en el pipeline.

---

## 4. Diferencia entre las pruebas de Staging y las de Producción

### Test Staging (`test-staging`) — Pruebas de Aceptación

Las pruebas de aceptación en staging son **exhaustivas y funcionales**. Utilizan Selenium para abrir el navegador, interactuar con la interfaz web y validar 8 casos de uso completos:

- Operaciones correctas: suma (2+3=5), resta (5-2=3), multiplicación (4×6=24), división (10/2=5)
- Casos de error: división por cero, entradas no numéricas
- Nuevas funcionalidades: potencia (2^3=8), módulo (10%3=1)

Cada caso verifica que el flujo completo funciona: el usuario introduce datos, el servidor los procesa, y el resultado correcto aparece en pantalla. Si cualquiera de estos 8 escenarios falla, el pipeline se detiene y producción no se actualiza.

### Smoke Test Producción (`smoke-test-production`) — Verificación mínima

El smoke test en producción es **deliberadamente superficial**. Solo verifica tres cosas: que la aplicación responde en la URL del ALB, que el título de la página contiene "Calculadora", y que el H1 dice exactamente "Calculadora". No realiza ninguna operación de la calculadora.

### Por qué esta diferencia

La lógica es que las pruebas de aceptación completas ya validaron el comportamiento funcional en staging, sobre la misma imagen Docker que ahora está en producción. Volver a ejecutar los 8 casos de Selenium en producción no aportaría evidencia nueva sobre si la aplicación funciona, solo alargaría el pipeline.

El smoke test en producción responde a una pregunta diferente y más urgente: **¿está el servicio levantado y respondiendo?** No si la lógica es correcta (eso ya fue validado), sino si el despliegue a producción se completó exitosamente y la aplicación es alcanzable. Si el smoke test falla, significa que algo falló en el proceso de despliegue mismo, no en el código.

Esta separación refleja un principio importante: no todas las pruebas tienen el mismo propósito ni deben ejecutarse en todos los entornos.

---

## 5. Qué le falta al pipeline para un ciclo DevOps completo

### 1. Monitoreo y Observabilidad post-despliegue

El pipeline actualmente termina después del smoke test. No hay mecanismo para detectar si la aplicación en producción empieza a fallar horas después del despliegue exitoso. En un ciclo DevOps completo, el "Deploy" no termina cuando el servicio está estable, sino cuando está demostrado que funciona bajo carga real.

**Por qué es importante:** Un smoke test confirma que la aplicación arranca, pero no detecta degradación de performance, errores intermitentes, o fugas de memoria que aparecen bajo carga real. Sin observabilidad, el equipo se entera de los problemas por los usuarios, no por el sistema.

**Cómo implementarlo:** AWS ya provee CloudWatch Logs configurado en el `main.tf` (el log group `/ecs/calculadora-${environment}-task` ya existe). Faltaría agregar métricas de la aplicación (tasa de errores HTTP 5xx, latencia p95) en CloudWatch, configurar alarmas que notifiquen al equipo (SNS → Slack/email) cuando superen umbrales, y potencialmente un job final en el pipeline que espere 5 minutos y verifique que las métricas de error están por debajo del umbral antes de marcar el pipeline como completamente exitoso.

### 2. Estrategia de rollback automático

Si el smoke test de producción falla, el pipeline falla, pero la infraestructura queda en un estado inconsistente: ECS tiene la nueva tarea pero sin responder. No hay ningún mecanismo automático para volver a la versión anterior.

**Por qué es importante:** En producción, cada minuto de caída tiene costo. Un rollback manual requiere que alguien identifique el SHA del commit anterior, edite variables, y re-ejecute el pipeline manualmente, lo cual puede tomar 20–30 minutos. Un rollback automático podría recuperar el servicio en 2–3 minutos.

**Cómo implementarlo:** Se podría añadir un job `rollback-prod` que se ejecute `if: failure()` después del smoke test. Este job recuperaría el SHA del último despliegue exitoso (guardado como variable en GitHub o en un parámetro de AWS SSM Parameter Store), ejecutaría `terraform apply` con esa imagen, y forzaría un nuevo deployment en ECS. Alternativamente, AWS ECS soporta Circuit Breaker nativo que puede revertir automáticamente un despliegue fallido al anterior basándose en el health check.

---

## 6. Experiencia implementando las nuevas funcionalidades y usando CI/CD

Implementar las dos nuevas funcionalidades de la calculadora —potencia y módulo— fue un proceso relativamente sencillo a nivel de código, pero el valor real lo aportó el pipeline de CI/CD que ya estaba en marcha.

El flujo fue claro: agregar la lógica en el backend, actualizar la plantilla HTML para incluir las nuevas opciones en el selector de operación, escribir las pruebas unitarias y agregar los casos al test de aceptación. Cada vez que hacíamos push, el pipeline nos daba feedback inmediato: si el formato del código no era correcto, Black lo decía antes de llegar a ningún test; si la lógica fallaba, pytest lo detectaba en segundos.

**Lo que resultó genuinamente útil del CI/CD:**

El ciclo de feedback rápido fue la ventaja más tangible. Antes de tener el pipeline, cometer un error de estilo o romper un test existente no se detectaba hasta que alguien revisaba el código manualmente, o peor, hasta que llegaba a producción. Con el pipeline, cada push produce evidencia objetiva de si el cambio está bien o no, en menos de 5 minutos. Eso cambia la forma de trabajar: se puede hacer un cambio pequeño, pushearlo, y saber de inmediato si rompió algo.

El despliegue automático a través de staging antes de llegar a producción también resultó valioso. En un par de ocasiones, la aplicación pasaba las pruebas unitarias localmente pero fallaba en staging por diferencias en la configuración del entorno. El pipeline lo detectó antes de que llegara a producción.

**Lo que no fue tan útil:**

Los tiempos de espera del pipeline completo se volvieron algo frustrantes en iteraciones rápidas. Cuando se hacía un cambio pequeño, esperar 15–20 minutos para ver la imagen en producción rompía el flujo de trabajo. En esos casos hubiera sido útil tener un modo de "fast feedback" que solo ejecutara las pruebas unitarias sin llegar a hacer deploy, para iteraciones locales.

También, el manejo de credenciales AWS temporales (con `AWS_SESSION_TOKEN` que expira) fue un punto de fricción constante: si el pipeline tardaba más de lo esperado o si los secretos no se actualizaban antes de correr el workflow, los jobs de Terraform fallaban con errores de autenticación que no eran obvios al principio. En un entorno real con credenciales permanentes o roles IAM de larga duración, esto no sería un problema.
