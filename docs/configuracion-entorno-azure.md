# Configuración del entorno Azure

1. Se preparó un entorno local y una suscripción de Microsoft Azure que permitiera el desarrollo de la platafoma de datos de Finbank. Las heramientas que se instalaron/ actualizaron por ahora fueron las siguientes:

- Git 2.45.0 windows.1 para el control de versiones
- Python 3.14.3 para la generación y el procesamiento local de los datos
- VS code 1.121.0 como entorno de desarrollo
- Azure CLI 2.89.1 para administrar Azure desde la terminal
- Terraform 1.15.8 Para aprovisionar infraestructura como código

2. También se instalaron las siguientes extesiones para VS code

- `hashicorp.terraform`: soporte para archivos de Terraform.
- `ms-azuretools.vscode-azureresourcegroups`: consulta de recursos de Azure.
- `ms-python.python`: desarrollo con Python.
- `redhat.vscode-yaml`: validación de archivos YAML.
[!NOTE]
Las extensiones específicas para SQL Server, Databricks y Jupyter se instalarán cuando sean necesarias.

3. Se aplicaron las siguientes medidas de seguridad:
- Contraseña actualizada.
- Microsoft Authenticator configurado.
- Verificación en dos pasos habilitada.

4. para el tema de costos la suscripción cuenta con crédito gratuito temporal y limite de gasto.
   También se configuró el presupuesto mensual `budget-finbank-dev` por USD 10, con alertas de costo real en los siguientes porcentajes:
    - 25 %
    - 50 %
    - 80 %
    - 100 %