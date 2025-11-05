"""
Esta es el modulo que incluye la clase de reproductor de musica
"""


class Player:
    """
    Esta clase crea un reproductor de musica
    """

    def play(self, song):
        """
        Reproduce la canción que recibio como parámetro

        Parameters:
        song (str): este es un string con el path de la canción 

        Returns:
        int: devuelve 1 si reproduce con exito, en caso de fracaso devuelve 0
        """
        print(f"Reproduciendo la canción: {song}")

    def stop(self):
        print("stopping")
