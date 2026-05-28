# TinyNes
developed for nfc card: https://www.waveshare.com/wiki/PN532_NFC_HAT
power button is pin 5 to 6 (board numbering)
reset button is 3.3v (1 or 17) to 11
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
    <keybind key="A-W-t">
      <action name="Execute">
        <command>/usr/bin/lxterminal</command>
    </action>
    <keybind key ="A-W-h">
      <action name="HideCursor"/>
    </keybind>
```
7. apt install fceux wtype
8. set background to nes logo or something
9. setup mouse autohide and taskbar autohide in labwc
10. set script to autorun at start
11. visudo to replace %sudo line with: %sudo   ALL=(ALL) NOPASSWD: ALL
12. copy wf-panel-pi.ini.* to ~/.config/wf-panel-pi
13. edit /home/nes/.config/labwc/autostart: add wtype -M alt -M logo -P h
14. copy showpanel and hidepanel to /usr/local/lib (check perms)
15. copy autostart to ~/.config/labwc/autostart (chmod +x)
