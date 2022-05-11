# Proyecto final Bootcamp Full-stack


### Backend

El stack para el back es Python + Flask + mongodb el front es React.

El back es una aplicación sencilla que permite gestionar los usuarios que van a utilizar el front.

La aplicación Flask tiene autenticación por sesión y solo tiene permiso para un usuario. La app permite crear, editar y eliminar usuarios.
Las contraseñas están encriptadas.
La app tiene un botón para cerrar sesión.

El front puede tener varios usuarios que se gestionan en el back.

### He utilizado:

- __pipenv__ para crear un entorno virtual
- __flask_pymongo__ para la conexión con mongodb
- __werkzeug__ para generar el hash de las contraseñas
- __Flask-cors__ para evitar conflictos con el servidor de react
- __Jinja__ como motor de plantillas para la maquetación
- __Postman__ para testar las peticiones a la API
- __Bootstrap__ para los estilos
- __font-awesome__ para los iconos
- __google fonts__ para añadir la tipofrafía Inter 

### Frontend

El frontend está basado en la aplicación del portfolio del curso pero tiene diferencias.

- He creado la app con create react app.
- He utilizado react router 6 por lo que he tenido que actualizar algunos componentes a la nueva sintaxis.
- En mi proyecto cada ítem de portfolio te dirige a una colección que contiene una galería de imágenes en massonry, si haces click en una imagen se amplia y se convierte en un light-box.
- Para mi aplicación he prescindido de los filtros y del blog.

Los dos proyecto están en GitHub por separado.

Finalmente los dos proyectos están alojados en Heroku.

__Acceso al backend__

usuario y contraseña:

Email: marcel@ibm.com

Password: abcd1234
