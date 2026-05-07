import db_config # 1

conexion = db_config.conectar_bd() # 2

if conexion: # 3
    print("¡Conexión exitosa a MySQL!") # 4
    conexion.close() # 5
else:
    print("Error: Revisa que MySQL esté encendido y las credenciales sean correctas.")