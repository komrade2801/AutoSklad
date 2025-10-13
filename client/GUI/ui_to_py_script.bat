for %%I in (.\ui\*.ui) do (
    echo Processing: ui\%%~nI.ui to ui_classes\%%~nI.py
	pyuic5 ui\%%~nI.ui -o ui_classes\Ui_%%~nI.py --import-from=..img
)

for %%I in (.\ui\widgets\*.ui) do (
    echo Processing: ui\widgets\%%~nI.ui to widgets\ui_classes\%%~nI.py
	pyuic5 ui\widgets\%%~nI.ui -o widgets\ui_classes\Ui_%%~nI.py --import-from=...img
)

pyrcc5 img\resources.qrc -o img\resources_rc.py
pyrcc5 img\resources_widget.qrc -o img\resources_widget_rc.py