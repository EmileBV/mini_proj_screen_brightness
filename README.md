# mini_proj_screen_brightness

Mini projet pour cours logique floue. 

Contrôleur de luminosité d'écran utilisant un fuzzy controller et un ajustement des C-Means quand l'utilisateur ajuste manuellement la luminosité de son écran soit par les contrôles Windows ou directement dans l'application.

L'application avait été pensé pour utiliser un capteur réel de l'uminosité ambiante mais pour la première ébauche, un simulateur est utilisé sous la forme d'un slider graphique dans l'application.

lib pythons utilisées:
- numpy
- scikit-fuzzy
- tkinter
- screen_brightness_control
- fuzzy-c-means
- opencv-python
  - dernière version de cv2 (4.6) ne marche pas, utiliser cette commande pour installer une version fonctionnelle:
  - ``pip install --force-reinstall --no-cache -U opencv-python==4.5.5.62   ``
