from selenium import webdriver
from selenium.webdriver.common.by import By
import pandas as pd
import numpy as np
import os

# Diccionario para mapear los días a números
days_map = {'Lun': 0, 'Mar': 1, 'Mie': 2, 'Jue': 3, 'Vie': 4, 'Sab': 5, 'Dom': 6}

# Función para convertir los días a números
def convert_days(days):
    return ', '.join([str(days_map[day]) for day in days.split(', ')])

# Import the courses_and_key csv file
df = pd.read_csv('webscraping/scripts/schedules/courses_and_keys.csv')

# Crear un archivo de registro para guardar las asignaturas que no pudieron ser añadidas
log_file = open('log.txt', 'w')

# Create a dictionary with the courses and keys
courses_and_key = dict(zip(df['course_name'], df['key']))

# Prepare the URL and Selenium driver
URL = "https://www.ssa.ingenieria.unam.mx/horarios.html"
driver = webdriver.Chrome()
driver.get(URL)

# Select the radio button "Horario por asignatura"
radio_button = driver.find_element(By.CSS_SELECTOR, 'input[name="optHorarioAsignatura"]')
radio_button.click()

if not os.path.exists('webscraping/scripts/schedules/results'):
    os.makedirs('webscraping/scripts/schedules/results')

# Now, for every subject in the dictionary, we will retrieve their schedules
for key in courses_and_key:    

    # Select the input field, clear it, and send the key
    input_field = driver.find_element(By.ID, 'clave')
    input_field.clear()
    input_field.send_keys(courses_and_key[key])
    input_field.submit()

    # List of tables
    tables = driver.find_elements(By.CLASS_NAME, 'table-horarios-custom')

    # New list to append the rows
    rows_list = []

    for table in tables:
        rows = table.find_elements(By.TAG_NAME, 'tr')
        
        for row in rows:
            cells = [cell.text for cell in row.find_elements(By.TAG_NAME, 'td')]
            rows_list.append(cells)

    # Delete the empty elements from rows_list
    rows_list = [row for row in rows_list if row]

    # Search for a row without the first 3 td elements (we know that it's a sub-schedule from the same course).
    # we could have a row with the form [ "L", '17:00 a 19:00', 'Lun, Mie', 'Y001' ] (Included lab) or ['17:00 a 19:00', 'Lun, Mie', 'Y001'] (Sub Theory Schedule)
    index = next((i for i, x in enumerate(rows_list) if len(x) <= 4 ), None)

    while index is not None:
        # Get the previous list
        prev_list = rows_list[index - 1]
        
        # Create a new list that contains the first three elements of the previous list and the elements of the original list
        if (rows_list[index][0] == 'L'):
            new_list = prev_list[:3] + rows_list[index]
        else: 
            new_list = prev_list[:3] + rows_list[index]
            new_list.insert(3, "T")
        
        # Replace the original list with the new list
        rows_list[index] = new_list
        
        # Search for the next index of the list where the row is of 3 elements or less
        index = next((i for i, x in enumerate(rows_list) if len(x) <= 4 and i > index), None)

    df = pd.DataFrame(rows_list)

    # Check if the DataFrame is empty
    if df.empty:
        # Log the name of the course that couldn't be added
        log_file.write(f'Could not add course: {key}\n')
        continue

    # Rename the columns
    df.columns = ['Clave', 'Grupo', 'Profesor', 'Tipo', 'Horario', 'Días', 'Salón', 'Cupo', 'Vacantes']

    # Drop the columns "Vacantes" and "Cupo

    df = df.drop(columns=['Vacantes', 'Cupo'])

    # Delete the empty rows
    df = df.replace('', np.nan)
    df = df.dropna()

    # Split the professor and the modality into two columns
    df[['Profesor', 'Modalidad']] = df['Profesor'].str.split('\n', expand=True)

    # Reset the index from 0 to n
    df.reset_index(drop=True, inplace=True)

    # Split the "Horario" column into two columns: "INI" y "FIN".
    df[['INI', 'FIN']] = df['Horario'].str.split(' a ', expand=True)

    # Elimina la columna original 'Horario'
    df = df.drop(columns=['Horario'])

    # Replace the "Días" column with the days of the week starting from Monday = 0 to Sunday = 6. For example "Mar, Jue" = "1, 3"
    df['Días'] = df['Días'].apply(convert_days)

    # Export the dataframe to a csv file with the name of the course in the folder "output"
    df.to_csv(f'webscraping/scripts/schedules/results/{key}.csv', index=False)

# Cerrar el archivo de registro
log_file.close()

# Cerrar el driver
driver.quit()