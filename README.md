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
    <keybind key ="A-W-h">
      <action name="HideCursor"/>
    </keybind>
```
7. apt install fceux
8. set background to nes logo or something
9. setup mouse autohide and taskbar autohide in labwc
10. set script to autorun at start
11. visudo to replace %sudo line with: %sudo   ALL=(ALL) NOPASSWD: ALL
12. vi /home/nes/.config/wf-panel-pi/wf-panel-pi.ini: add autohide=true
13. edit /home/nes/.config/labwc/autostart: add wtype -M alt -M logo -P h
