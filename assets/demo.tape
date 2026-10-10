# container-autopsy demo GIF — generate with: vhs demo.tape
Output demo.gif
Set FontSize 20
Set Width 980
Set Height 640
Set Theme "Dracula"
Set Shell bash

Type "python container_autopsy.py my-dead-app" Enter
Sleep 1s
Wait@500ms /Autopsy report/
Sleep 4s
