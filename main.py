import sys

from PyQt5.QtCore import QDateTime
from PyQt5.QtWidgets import *
######################################################
### import de la clase para la coneccion con la bd ###
######################################################
from SQL import DatabaseConnection



class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()

        ################################################################################
        #### acá cargamos la hoja de estilos que esta ubicada en el Dic. "resources" ###
        ################################################################################
        self.loadStyles("resources/style.qss")

    def loadStyles(self, stylesheetFile):
        with open(stylesheetFile, "r") as file:
            self.setStyleSheet(file.read())

    def initUI(self):
        self.statusBar().showMessage('Listo')
        self.setGeometry(300, 300, 800, 600)
        self.setWindowTitle('Gestión de Tareas')

        # Botón de Refrescar
        self.refreshButton = QPushButton("Refrescar", self)
        self.refreshButton.clicked.connect(self.refreshContent)

        # Barra de herramientas con el botón de refrescar
        self.toolbar = self.addToolBar("Refrescar")
        self.toolbar.addWidget(self.refreshButton)

        self.table_widget = MyTableWidget(self)
        self.setCentralWidget(self.table_widget)
        self.show()

    def refreshContent(self):
        self.table_widget.loginTab.refreshContent()
        self.table_widget.tab2.refreshContent()  # Asegúrate de que tab2 sea RoleAssignmentTab
        self.table_widget.tab3.refreshContent()  # Asegúrate de que tab3 sea ProjectManagementTab
        self.table_widget.tab4.refreshContent()  # Asegúrate de que tab4 sea GoalsTab
        self.table_widget.tab5.refreshContent()


class LoginTab(QWidget):
    def __init__(self, parentWidget):
        super().__init__()
        self.parentWidget = parentWidget  # Referencia al widget padre (MyTableWidget)
        self.initUI()
        self.loadNonAdminUsers()  # Cargar usuarios no administradores

    def initUI(self):
        self.layout = QVBoxLayout(self)

        # Formulario de inicio de sesión
        self.loginFormLayout = QFormLayout()
        self.usernameLineEdit = QLineEdit()
        self.passwordLineEdit = QLineEdit()
        self.passwordLineEdit.setEchoMode(QLineEdit.Password)  # Ocultar contraseña
        self.loginButton = QPushButton("Iniciar Sesión")
        self.loginFormLayout.addRow("Nombre de Usuario:", self.usernameLineEdit)
        self.loginFormLayout.addRow("Contraseña:", self.passwordLineEdit)
        self.loginFormLayout.addRow(self.loginButton)

        # Formulario de registro
        self.registerFormLayout = QFormLayout()
        self.regUsernameLineEdit = QLineEdit()
        self.regEmailLineEdit = QLineEdit()
        self.regPasswordLineEdit = QLineEdit()
        self.regPasswordLineEdit.setEchoMode(QLineEdit.Password)
        self.isAdminCheckBox = QCheckBox("Es administrador")
        self.userComboBox = QComboBox()
        self.registerButton = QPushButton("Registrar")
        self.registerFormLayout.addRow("Nombre de Usuario:", self.regUsernameLineEdit)
        self.registerFormLayout.addRow("Correo:", self.regEmailLineEdit)
        self.registerFormLayout.addRow("Contraseña:", self.regPasswordLineEdit)
        self.registerFormLayout.addRow("Usuario Asociado:", self.userComboBox)
        self.registerFormLayout.addRow(self.isAdminCheckBox)
        self.registerFormLayout.addRow(self.registerButton)

        self.layout.addLayout(self.loginFormLayout)
        self.layout.addLayout(self.registerFormLayout)
        self.setLayout(self.layout)

        self.loginButton.clicked.connect(self.login)
        self.registerButton.clicked.connect(self.register)
        self.userComboBox.currentIndexChanged.connect(self.onUserSelected)

    def refreshContent(self):
        self.loadNonAdminUsers()

    def loadNonAdminUsers(self):
        db = DatabaseConnection()
        connection = db.connect()
        if connection:
            cursor = connection.cursor()
            cursor.execute("SELECT id_usuario, nombre_usuario FROM usuarios WHERE es_admin = FALSE")
            users = cursor.fetchall()
            self.userComboBox.addItem("ADMIN", None)  # Opción para poder realmente tener un admin.
            for user in users:
                self.userComboBox.addItem(user[1], user[0])
            cursor.close()
            db.close()

    def onUserSelected(self, index):
        is_new_user = self.userComboBox.currentData() is None
        self.isAdminCheckBox.setEnabled(is_new_user)
        self.regUsernameLineEdit.setEnabled(is_new_user)
        self.regEmailLineEdit.setEnabled(is_new_user)

        if not is_new_user:
            selected_user_id = self.userComboBox.currentData()
            self.fillUserInfo(selected_user_id)
        else:
            self.regUsernameLineEdit.clear()
            self.regEmailLineEdit.clear()

    def fillUserInfo(self, user_id):
        db = DatabaseConnection()
        connection = db.connect()
        if connection:
            cursor = connection.cursor()
            cursor.execute("SELECT nombre_usuario, correo FROM usuarios WHERE id_usuario = %s", (user_id,))
            user_info = cursor.fetchone()
            if user_info:
                self.regUsernameLineEdit.setText(user_info[0])
                self.regEmailLineEdit.setText(user_info[1])
            cursor.close()
            db.close()

    def login(self):
        username = self.usernameLineEdit.text()
        password = self.passwordLineEdit.text()

        db = DatabaseConnection()
        connection = db.connect()
        if connection:
            cursor = connection.cursor()
            cursor.execute("SELECT password, es_admin FROM usuarios WHERE nombre_usuario = %s", (username,))
            user = cursor.fetchone()
            if user and user[0] == password:
                print("Inicio de sesión exitoso")
                self.parentWidget.unlockTabs()
            else:
                print("Usuario o contraseña incorrectos")
            cursor.close()
            db.close()

    def register(self):
        username = self.regUsernameLineEdit.text()
        email = self.regEmailLineEdit.text()
        password = self.regPasswordLineEdit.text()
        is_admin = self.isAdminCheckBox.isChecked()
        associated_user_id = self.userComboBox.currentData() if not is_admin else None

        db = DatabaseConnection()
        connection = db.connect()
        if connection:
            cursor = connection.cursor()
            if is_admin or associated_user_id is None:
                cursor.execute("INSERT INTO usuarios (nombre_usuario, correo, password, es_admin) VALUES (%s, %s, %s, %s)",
                               (username, email, password, is_admin))
            else:
                cursor.execute("UPDATE usuarios SET password = %s WHERE id_usuario = %s",
                               (password, associated_user_id))
            connection.commit()
            cursor.close()
            db.close()






class MyTableWidget(QWidget):
    def __init__(self, parent):
        super(QWidget, self).__init__(parent)
        self.layout = QVBoxLayout(self)

        # Inicialización de las pestañas
        self.tabs = QTabWidget()
        self.loginTab = LoginTab(self)  # Se pasa self como referencia a LoginTab
        self.tab1 = QWidget()  # Pestaña "registro de equipos"
        self.tab2 = RoleAssignmentTab()  # Pestaña "asignación de roles"
        self.tab3 = ProjectManagementTab()  # Pestaña "Gestión de proyectos"
        self.tab4 = GoalsTab()  # Pestaña "Metas"
        self.tab5 = ProgressTab()  # Pestaña "Progreso Total"

        # Agregar pestañas al QTabWidget
        self.tabs.addTab(self.loginTab, "Inicio de Sesión")
        self.tabs.addTab(self.tab1, "Registro de Equipos")
        self.tabs.addTab(self.tab2, "Asignación de Roles")
        self.tabs.addTab(self.tab3, "Gestión de Proyectos")
        self.tabs.addTab(self.tab4, "Metas")
        self.tabs.addTab(self.tab5, "Progreso Total")

        self.tab1.layout = QVBoxLayout(self)
        self.formLayout = QFormLayout()
        self.nameLineEdit = QLineEdit()
        self.memberNameLineEdit1 = QLineEdit()
        self.memberNameLineEdit2 = QLineEdit()
        self.memberNameLineEdit3 = QLineEdit()
        self.memberNameLineEdit4 = QLineEdit()
        self.formLayout.addRow("Nombre del Equipo:", self.nameLineEdit)
        self.registerTeamButton = QPushButton("Registrar Equipo")
        self.formLayout.addRow("Nombre del integrante:", self.memberNameLineEdit1)
        self.formLayout.addRow("Nombre del integrante:", self.memberNameLineEdit2)
        self.formLayout.addRow("Nombre del integrante:", self.memberNameLineEdit3)
        self.formLayout.addRow("Nombre del integrante:", self.memberNameLineEdit4)
        self.formLayout.addRow(self.registerTeamButton)
        self.tab1.setLayout(self.formLayout)


        # Configurar el layout principal
        self.layout.addWidget(self.tabs)
        self.setLayout(self.layout)
        self.registerTeamButton.clicked.connect(self.register_team)
        # Inicialmente, desactivar todas las pestañas excepto la de inicio de sesión

        self.lockTabs()

    def refreshContent(self):
        self.loadTeams()
        self.updateProjectsTable()
    def lockTabs(self):
        for index in range(1, self.tabs.count()):
            self.tabs.setTabEnabled(index, False)

    def unlockTabs(self):
        for index in range(1, self.tabs.count()):
            self.tabs.setTabEnabled(index, True)

    def register_team(self):
        team_name = self.nameLineEdit.text()
        member_names = [
            self.memberNameLineEdit1.text(),
            self.memberNameLineEdit2.text(),
            self.memberNameLineEdit3.text(),
            self.memberNameLineEdit4.text()
        ]

        if not team_name or not any(member_names):
            print("Información del equipo o integrantes incompleta")
            return

        db = DatabaseConnection()
        connection = db.connect()
        if connection:
            try:
                cursor = connection.cursor()
                # Registrar equipo
                cursor.execute("INSERT INTO equipos (nombre_equipo) VALUES (%s)", (team_name,))
                team_id = cursor.lastrowid  # ID del equipo recién insertado

                # Registrar integrantes
                for member_name in member_names:
                    if member_name:  # Solo inserta si el campo no está vacío
                        cursor.execute("INSERT INTO usuarios (nombre_usuario, id_equipo) VALUES (%s, %s)",
                                       (member_name, team_id))

                connection.commit()
                print("Equipo e integrantes registrados exitosamente")
            except Exception as e:
                print("Error al registrar equipo e integrantes:", e)
                connection.rollback()
            finally:
                cursor.close()
                db.close()
        else:
            print("No se pudo conectar a la base de datos.")



class RoleAssignmentTab(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.loadRoles()
        self.loadUsers()

    def initUI(self):
        self.layout = QVBoxLayout(self)

        # Sección para asignar roles a los usuarios
        self.assignRoleLayout = QHBoxLayout()
        self.userComboBox = QComboBox()  # ComboBox para usuarios
        self.roleComboBox = QComboBox()  # ComboBox para roles
        self.assignRoleButton = QPushButton("Asignar Rol")
        self.assignRoleLayout.addWidget(QLabel("Usuario:"))
        self.assignRoleLayout.addWidget(self.userComboBox)
        self.assignRoleLayout.addWidget(QLabel("Rol:"))
        self.assignRoleLayout.addWidget(self.roleComboBox)
        self.assignRoleButton.clicked.connect(self.assignRoleToUser)
        self.layout.addLayout(self.assignRoleLayout)
        self.layout.addWidget(self.assignRoleButton)

        self.usersTable = QTableWidget()
        self.usersTable.setColumnCount(2)  # Dos columnas: ID y Nombre
        self.usersTable.setHorizontalHeaderLabels(["ID Usuario", "Nombre Usuario"])
        self.usersTable.horizontalHeader().setStretchLastSection(True)
        self.usersTable.setSelectionBehavior(QTableWidget.SelectRows)
        self.layout.addWidget(self.usersTable)

        # Sección para agregar nuevos roles
        self.addRoleLayout = QHBoxLayout()
        self.newRoleLineEdit = QLineEdit()
        self.addRoleButton = QPushButton("Añadir Nuevo Rol")
        self.addRoleButton.clicked.connect(self.addNewRole)
        self.addRoleLayout.addWidget(QLabel("Nombre del Rol:"))
        self.addRoleLayout.addWidget(self.newRoleLineEdit)
        self.layout.addLayout(self.addRoleLayout)
        self.layout.addWidget(self.addRoleButton)

        self.setLayout(self.layout)

    def refreshContent(self):
        self.loadRoles()
        self.loadUsers()

        # Actualiza la tabla de usuarios si existe
        # Asegúrate de implementar updateUsersTable()
        if hasattr(self, 'updateUsersTable'):
            self.updateUsersTable()

    def loadRoles(self):
        db = DatabaseConnection()
        connection = db.connect()
        if connection:
            cursor = connection.cursor()
            cursor.execute("SELECT nombre_rol FROM roles")
            roles = cursor.fetchall()
            for role in roles:
                self.roleComboBox.addItem(role[0])
            cursor.close()
            db.close()

    def loadUsers(self):
        db = DatabaseConnection()
        connection = db.connect()
        if connection:
            cursor = connection.cursor()
            cursor.execute("SELECT id_usuario, nombre_usuario FROM usuarios")
            users = cursor.fetchall()
            for user in users:
                self.userComboBox.addItem(user[1], user[0])
            cursor.close()
            db.close()

        db = DatabaseConnection()
        connection = db.connect()
        if connection:
            cursor = connection.cursor()
            cursor.execute("SELECT id_usuario, nombre_usuario FROM usuarios")
            users = cursor.fetchall()
            self.usersTable.setRowCount(len(users))
            for row_number, user in enumerate(users):
                self.usersTable.setItem(row_number, 0, QTableWidgetItem(str(user[0])))
                self.usersTable.setItem(row_number, 1, QTableWidgetItem(user[1]))
            cursor.close()
            db.close()

    def assignRoleToUser(self):
        user_id = self.userComboBox.currentData()
        selected_role = self.roleComboBox.currentText()

        db = DatabaseConnection()
        connection = db.connect()
        if connection:
            cursor = connection.cursor()
            cursor.execute("UPDATE roles SET id_usuario = %s WHERE nombre_rol = %s", (user_id, selected_role))
            connection.commit()
            cursor.close()
            db.close()

    def addNewRole(self):
        new_role = self.newRoleLineEdit.text()
        db = DatabaseConnection()
        connection = db.connect()
        if connection:
            cursor = connection.cursor()
            cursor.execute("INSERT INTO roles (nombre_rol) VALUES (%s)", (new_role,))
            connection.commit()
            cursor.close()
            db.close()
            self.loadRoles()  # Recargar los roles para incluir el nuevo


class ProjectManagementTab(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.loadTeams()

    def initUI(self):
        self.layout = QVBoxLayout(self)

        ##########################################
        # formulario para crear el proyecto nuevo
        ##########################################
        self.projectFormLayout = QFormLayout()
        self.projectNameLineEdit = QLineEdit()
        self.projectDeadlineDateEdit = QDateEdit()
        self.projectGoalsTextEdit = QLineEdit()
        self.createProjectButton = QPushButton("Crear Proyecto")
        self.createProjectButton.clicked.connect(self.addProject)
        self.teamComboBox = QComboBox()
        self.projectFormLayout.insertRow(0, "Equipo:", self.teamComboBox)

        self.projectFormLayout.addRow("Nombre del Proyecto:", self.projectNameLineEdit)
        self.projectFormLayout.addRow("Fecha de Finalización:", self.projectDeadlineDateEdit)
        self.projectFormLayout.addRow("Metas:", self.projectGoalsTextEdit)
        self.projectFormLayout.addRow(self.createProjectButton)

        ##########################################
        # con esto mostramos la tabla en la app
        ##########################################
        self.projectsTable = QTableWidget()
        self.projectsTable.setColumnCount(3)
        self.projectsTable.setHorizontalHeaderLabels(["Nombre del Proyecto", "Fecha de Finalización", "Metas"])
        self.updateProjectsTable()

        ##########################################
        # agregar formularios y tabla al layout
        ##########################################
        self.layout.addLayout(self.projectFormLayout)
        self.layout.addWidget(QLabel("Proyectos Existentes"))
        self.layout.addWidget(self.projectsTable)

        self.setLayout(self.layout)

    def refreshContent(self):
        self.loadTeams()
        self.updateProjectsTable()


    def loadTeams(self):
        # Limpia el ComboBox antes de cargar nuevos datos
        self.teamComboBox.clear()

        db = DatabaseConnection()
        connection = db.connect()
        if connection:
            cursor = connection.cursor()
            cursor.execute("SELECT id_equipo, nombre_equipo FROM equipos")
            teams = cursor.fetchall()
            for team in teams:
                self.teamComboBox.addItem(team[1], team[0])
            cursor.close()
            db.close()
    def addProject(self):
        ##########################################
        # Recoger los datos del formulario
        ##########################################
        name = self.projectNameLineEdit.text()
        deadline = self.projectDeadlineDateEdit.date().toString("yyyy-MM-dd")
        goal_description = "Meta principal: " + self.projectGoalsTextEdit.text()
        start_date = QDateTime.currentDateTime().toString("yyyy-MM-dd")
        team_id = self.teamComboBox.currentData()

        ##########################################
        # Insertar los datos en la base de datos
        ##########################################
        db = DatabaseConnection()
        connection = db.connect()
        if connection:
            cursor = connection.cursor()
            cursor.execute(
                "INSERT INTO proyectos (nombre_proyecto, descripcion, fecha_inicio, fecha_finalizacion) VALUES (%s, %s, %s, %s)",
                (name, goal_description, start_date, deadline))
            connection.commit()
            cursor.close()
            db.close()
        #################################################
        # Actualizar la tabla en la interfaz de usuario
        #################################################
        self.updateProjectsTable()

    def updateProjectsTable(self):
        ###################################################################
        # Recuperar proyectos de la base de datos y actualizar la tabla
        ###################################################################
        db = DatabaseConnection()
        connection = db.connect()
        if connection:
            cursor = connection.cursor()
            cursor.execute("SELECT nombre_proyecto, fecha_finalizacion, descripcion FROM proyectos")
            projects = cursor.fetchall()
            self.projectsTable.setRowCount(len(projects))
            for row_number, project in enumerate(projects):
                self.projectsTable.setItem(row_number, 0, QTableWidgetItem(project[0]))
                self.projectsTable.setItem(row_number, 1, QTableWidgetItem(project[1].strftime("%Y-%m-%d")))
                self.projectsTable.setItem(row_number, 2, QTableWidgetItem(project[2]))
            cursor.close()
            db.close()

class GoalsTab(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.loadRoles()
        self.loadProjects()

    def initUI(self):
        self.layout = QVBoxLayout(self)

        self.goalsFormLayout = QFormLayout()
        self.goalNameLineEdit = QLineEdit()
        self.goalRoleComboBox = QComboBox()  # Lista desplegable para roles
        self.goalProjectComboBox = QComboBox()  # Lista desplegable para proyectos
        self.goalDescriptionTextEdit = QTextEdit()
        self.goalDeadlineDateEdit = QDateEdit()
        self.goalDeadlineDateEdit.setCalendarPopup(True)
        self.goalTypeGroup = QButtonGroup(self)
        self.isMainGoalRadioButton = QRadioButton("Meta principal")
        self.isSecondaryGoalRadioButton = QRadioButton("Meta secundaria")
        self.goalTypeGroup.addButton(self.isMainGoalRadioButton)
        self.goalTypeGroup.addButton(self.isSecondaryGoalRadioButton)
        self.addGoalButton = QPushButton("Agregar Meta")
        self.addGoalButton.clicked.connect(self.addGoal)

        self.goalsFormLayout.addRow("Nombre de la Meta:", self.goalNameLineEdit)
        self.goalsFormLayout.addRow("Rol Asignado:", self.goalRoleComboBox)
        self.goalsFormLayout.addRow("Proyecto Asignado:", self.goalProjectComboBox)
        self.goalsFormLayout.addRow("Descripción:", self.goalDescriptionTextEdit)
        self.goalsFormLayout.addRow("Fecha Límite:", self.goalDeadlineDateEdit)
        self.goalsFormLayout.addRow(self.isMainGoalRadioButton)
        self.goalsFormLayout.addRow(self.isSecondaryGoalRadioButton)
        self.goalsFormLayout.addRow(self.addGoalButton)

        self.layout.addLayout(self.goalsFormLayout)
        self.setLayout(self.layout)

    def refreshContent(self):
        self.loadRoles()
        self.loadProjects()

    def loadRoles(self):
        db = DatabaseConnection()
        connection = db.connect()
        if connection:
            cursor = connection.cursor()
            cursor.execute("SELECT nombre_rol FROM roles")
            roles = cursor.fetchall()
            for role in roles:
                self.goalRoleComboBox.addItem(role[0])
            cursor.close()
            db.close()

    def loadProjects(self):
        db = DatabaseConnection()
        connection = db.connect()
        if connection:
            cursor = connection.cursor()
            cursor.execute("SELECT id_proyecto, nombre_proyecto FROM proyectos")
            projects = cursor.fetchall()
            for project in projects:
                self.goalProjectComboBox.addItem(project[1], project[0])
            cursor.close()
            db.close()

    def addGoal(self):
        goal_name = self.goalNameLineEdit.text()
        role = self.goalRoleComboBox.currentText()
        project_id = self.goalProjectComboBox.currentData()
        description = self.goalDescriptionTextEdit.toPlainText()
        deadline = self.goalDeadlineDateEdit.date().toString("yyyy-MM-dd")
        goal_type = "Principal" if self.isMainGoalRadioButton.isChecked() else "Secundaria"

        if not goal_name or not description:
            print("Nombre de la meta y descripción no pueden estar en blanco.")
            return

        db = DatabaseConnection()
        connection = db.connect()
        if connection:
            cursor = connection.cursor()
            cursor.execute("INSERT INTO tareas (descripcion, estado, fecha_limite, id_proyecto, id_usuario_asignado) VALUES (%s, %s, %s, %s, %s)",
                           (description, goal_type, deadline, project_id, None))  # Asumiendo que no hay un usuario asignado inicialmente
            connection.commit()
            cursor.close()
            db.close()
            print("Meta agregada correctamente.")



#############################################################################################################################################################################
# a futuro le agregare esto, aquí las funciones para interactuar con la base de datos(falta crear nueva apartado dentro de la tabla proyectos). de la pestaña "metas" ##
#############################################################################################################################################################################

class ProgressTab(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.loadTasks()

    def initUI(self):
        self.layout = QVBoxLayout(self)

        # Contenedor principal
        mainContainer = QVBoxLayout()

        # Lista de Tareas
        tasksLayout = QHBoxLayout()
        tasksLayout.addWidget(QLabel("Tarea:"))
        self.tasksComboBox = QComboBox()
        tasksLayout.addWidget(self.tasksComboBox)
        mainContainer.addLayout(tasksLayout)

        # Botones de Opción para el Estado de la Tarea
        statusLayout = QHBoxLayout()
        statusLayout.addWidget(QLabel("Estado:"))
        self.statusGroup = QButtonGroup(self)
        self.readyRadioButton = QRadioButton("Lista")
        self.inProgressRadioButton = QRadioButton("En Progreso")
        self.needsMorePeopleRadioButton = QRadioButton("Necesita Más Gente")
        self.statusGroup.addButton(self.readyRadioButton)
        self.statusGroup.addButton(self.inProgressRadioButton)
        self.statusGroup.addButton(self.needsMorePeopleRadioButton)
        statusLayout.addWidget(self.readyRadioButton)
        statusLayout.addWidget(self.inProgressRadioButton)
        statusLayout.addWidget(self.needsMorePeopleRadioButton)
        mainContainer.addLayout(statusLayout)

        # Botón para actualizar el estado de la tarea
        self.updateStatusButton = QPushButton("Actualizar Estado")
        self.updateStatusButton.clicked.connect(self.updateTaskStatus)
        mainContainer.addWidget(self.updateStatusButton)

        # Medidor de Progreso
        progressLayout = QVBoxLayout()
        progressLabel = QLabel("Progreso Total:")
        progressLabel.setContentsMargins(0, 0, 0, -5)  # Reduce el margen inferior
        progressLayout.addWidget(progressLabel)
        self.progressMeter = QProgressBar()
        progressLayout.addWidget(self.progressMeter)
        mainContainer.addLayout(progressLayout)

        # Aplicar el contenedor principal al layout
        self.layout.addLayout(mainContainer)
        self.setLayout(self.layout)

    def refreshContent(self):
        self.loadTasks()
        self.calculateTotalProgress()
    def loadTasks(self):
        db = DatabaseConnection()
        connection = db.connect()
        if connection:
            cursor = connection.cursor()
            cursor.execute("SELECT id_tarea, descripcion FROM tareas")
            tasks = cursor.fetchall()
            for task in tasks:
                self.tasksComboBox.addItem(task[1], task[0])  # Descripción de la tarea y su ID
            cursor.close()
            db.close()
        self.calculateTotalProgress()

    def updateTaskStatus(self):
        selected_task_id = self.tasksComboBox.currentData()
        new_status = ""
        points = 0

        if self.readyRadioButton.isChecked():
            new_status = "Lista"
            points = 3
        elif self.inProgressRadioButton.isChecked():
            new_status = "En Progreso"
            points = 2
        elif self.needsMorePeopleRadioButton.isChecked():
            new_status = "Necesita Más Gente"
            points = 0

        db = DatabaseConnection()
        connection = db.connect()
        if connection:
            cursor = connection.cursor()
            cursor.execute("UPDATE tareas SET estado = %s, puntos_progreso = %s WHERE id_tarea = %s",
                           (new_status, points, selected_task_id))
            connection.commit()
            cursor.close()
            db.close()
        self.calculateTotalProgress()

    def calculateTotalProgress(self):
        db = DatabaseConnection()
        connection = db.connect()
        if connection:
            cursor = connection.cursor()
            cursor.execute("SELECT SUM(puntos_progreso) FROM tareas")
            total_points = cursor.fetchone()[0]
            cursor.close()
            db.close()
            self.progressMeter.setMaximum(3 * self.tasksComboBox.count())  # Máximo posible
            self.progressMeter.setValue(total_points if total_points else 0)




def main():
    app = QApplication(sys.argv)
    ex = MainWindow()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
