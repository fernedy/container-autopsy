# container-autopsy demo GIF — kill a real container, autopsy it.
#   local:   cd assets && vhs demo.tape            (needs docker CLI + a docker daemon)
#   docker:  docker run --rm -v "<repo parent>:/work" -v /var/run/docker.sock:/var/run/docker.sock \
#              -w /work/container-autopsy/assets vhs-ops:1 demo.tape
Output demo.gif
Set FontSize 18
Set Width 1000
Set Height 640
Set Theme "Dracula"
Set TypingSpeed 20ms

Type "docker rm -f demo-app >/dev/null 2>&1; docker run --name demo-app busybox sh -c 'exit 137'" Enter
Sleep 8s
Type "python3 ../container_autopsy.py demo-app" Enter
Sleep 6s
Type "docker rm demo-app >/dev/null" Enter
Sleep 2s
