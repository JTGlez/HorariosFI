from selenium import webdriver
from selenium.webdriver.common.by import By
import pandas as pd
import os

# Lista de claves
careers_keys = ['2232', '2221', '2220', '2223', '2222', '2228', '2231', '2225', '2224', '2229', '2227', '2226', '2230', '2233', '2234']

# Crear el driver
driver = webdriver.Chrome()

# Crear un DataFrame vacío para almacenar los datos
df = pd.DataFrame(columns=['course_name', 'key'])

# Recorrer cada clave
for key in careers_keys:
    # Generar la URL
    URL = f"https://www.dgae-siae.unam.mx/educacion/planes.php?acc=est&pde={key}"
    
    # Navegar a la URL
    driver.get(URL)
    
    # Encontrar todas las filas que contienen una celda con la clase "CellIco" y un elemento input como hijo
    rows = driver.find_elements(By.XPATH, "//tr[td/@class='CellIco' and td/input]")
    
    # Extraer los datos de cada fila y agregarlos al DataFrame
    for row in rows:
        input_field = row.find_element(By.XPATH, ".//input[@name='asg']")
        course_name = row.find_element(By.XPATH, ".//td[@class='CellDat']").text
        key = input_field.get_attribute('value')
        df = df._append({'course_name': course_name, 'key': key}, ignore_index=True)

if not os.path.exists('webscraping/scripts/keys/results'):
    os.makedirs('webscraping/scripts/keys/results')

# Especificar la ruta completa al guardar el archivo CSV
df.to_csv('webscraping/scripts/keys/results/courses_and_keys.csv', index=False)

# Cerrar el driver
driver.quit()