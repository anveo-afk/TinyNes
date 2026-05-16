# TinyNes
1. setup dtoverlay for power button
2. the default pi os installer makes the root partition too small, make it bigger with gparted (might as well make a /roms mount while you're at it)
3. run raspiconfig and enable sspi
4. copy roms to /roms/nes/\*.nes
5. modify the logind conf in /etc/systemd for the power button
6. edit /etc/xdg/labwc/rc.xml:
```
    <keybind key="XF86PowerOff">
      <action name="Execute">
        <command>systemctl poweroff</command>
      </action>
    </keybind>
```
7. apt install fceux
