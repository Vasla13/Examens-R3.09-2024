import sys
import socket
import threading
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QPushButton, QTextEdit, QLineEdit, QLabel, QWidget
from PyQt5.QtCore import Qt, QMetaObject, Q_ARG


class ServerApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Le serveur de tchat")
        self.setGeometry(100, 100, 500, 300)
        
        self.server = None
        self.clients = [] 
        self.is_running = False
        
        self.layout = QVBoxLayout()
        self.init_ui()
        
        central_widget = QWidget()
        central_widget.setLayout(self.layout)
        self.setCentralWidget(central_widget)
        
    def init_ui(self):
        self.host_label = QLabel("Serveur :")
        self.layout.addWidget(self.host_label)
        self.host_input = QLineEdit("127.0.0.1")
        self.layout.addWidget(self.host_input)

        self.port_label = QLabel("Port :")
        self.layout.addWidget(self.port_label)
        self.port_input = QLineEdit("4200")
        self.layout.addWidget(self.port_input)

        self.max_clients_label = QLabel("Nombre de clients maximum :")
        self.layout.addWidget(self.max_clients_label)
        self.max_clients_input = QLineEdit("5")
        self.layout.addWidget(self.max_clients_input)

        self.log_display = QTextEdit()
        self.log_display.setReadOnly(True)
        self.layout.addWidget(self.log_display)

        self.toggle_button = QPushButton("Démarrage du serveur")
        self.toggle_button.clicked.connect(self.toggle_server)
        self.layout.addWidget(self.toggle_button)

        self.quit_button = QPushButton("Quitter")
        self.quit_button.clicked.connect(self.close_server)
        self.layout.addWidget(self.quit_button)
    
    def log(self, message):
        QMetaObject.invokeMethod(self.log_display, "append", Qt.QueuedConnection, Q_ARG(str, message))
        
    def toggle_server(self):
        if self.is_running:
            self.stop_server()
        else:
            self.start_server()
            
    def start_server(self):
        try:
            host = self.host_input.text()
            port = int(self.port_input.text())
            max_clients = int(self.max_clients_input.text())
            
            self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server.bind((host, port))
            self.server.listen(max_clients)
            
            self.log(f"Serveur démarré sur {host}:{port} avec un maximum de {max_clients} clients.")
            self.toggle_button.setText("Arrêt du serveur")
            self.is_running = True
            
            # Thread pour accepter les clients
            threading.Thread(target=self.accept_clients, daemon=True).start()
        except ValueError:
            self.log("Erreur : Le port et le nombre maximum de clients doivent être des nombres entiers.")
        except Exception as e:
            self.log(f"Erreur lors du démarrage : {e}")
            
    def stop_server(self):
        try:
            if self.server:
                self.server.close()
            for client in self.clients:
                client.close()
            self.clients = []
            self.server = None
            self.is_running = False
            self.log("Serveur arrêté.")
            self.toggle_button.setText("Démarrage du serveur")
        except Exception as e:
            self.log(f"Erreur lors de l'arrêt : {e}")
        # Question 1 : Pour une déconnexion propre côté client :
        #  Chaque client devrait recevoir un message indiquant que le serveur est fermé. note : ca marche pas 

    def accept_clients(self):
        while self.is_running:
            try:
                client_socket, client_address = self.server.accept()

                if len(self.clients) >= int(self.max_clients_input.text()):
                    self.log(f"Connexion refusée : {client_address}. Nombre maximum de clients atteint.")
                    client_socket.send("Serveur complet. Connexion refusée.".encode("utf-8"))
                    client_socket.close()
                    continue

                self.clients.append(client_socket)
                self.log(f"Client connecté : {client_address}")

                threading.Thread(target=self.handle_client, args=(client_socket,), daemon=True).start()
            except Exception as e:
                self.log(f"Erreur lors de l'acceptation d'un client : {e}")
                break

    def handle_client(self, client_socket):
        try:
            while True:
                message = client_socket.recv(1024).decode("utf-8")
                if not message:
                    break
                if message == "deco-server":
                    self.log("Client déconnecté.")
                    break
                self.log(f"Message reçu : {message}")
                self.broadcast_message(message, client_socket)
        except Exception as e:
            self.log(f"Erreur lors de la réception : {e}")
        finally:
            client_socket.close()
            if client_socket in self.clients:
                self.clients.remove(client_socket)
            # Question 1 : Pour une déconnexion correcte côté client :
            #  Il faut envoyer un message au serveur pour signaler la déconnexion (en utilisant le message : "deco-server").
            #  Gérer les exceptions lors de cette fermeture pour éviter les plantages en cas d'erreur réseau.

    def broadcast_message(self, message, sender_socket):
        for client in self.clients:
            if client != sender_socket:
                try:
                    client.send(message.encode("utf-8"))
                except Exception as e:
                    self.log(f"Erreur lors de l'envoi au client : {e}")
        # Question 2 : Pour gérer plusieurs clients simultanément :
        #  Il faut créer un thread pour chaque client lors de sa connexion. Cela évite qu'un client bloque le serveur.
        #  Utiliser une liste (self.clients) pour stocker toutes les connexions actives.
        #  Diffuser les messages à tous les clients connectés via une boucle sur cette liste.

    def close_server(self):
        self.stop_server()
        self.close()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    server_app = ServerApp()
    server_app.show()
    sys.exit(app.exec_())
