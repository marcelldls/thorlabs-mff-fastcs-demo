# FastCS demo device

Get started:
```
pip install -r requirements.txt
```

Start the controller
```
python controller.py run config.yaml
```

For EPICS gui: Start Phoebus (requires Docker)
```
bash phoebus.sh
```

For REST gui: Open `localhost:8080/docs`
```
firefox localhost:8080/docs
```