from core.scan_history import ScanHistory
sh = ScanHistory()
sid = sh.record_start("test.com", "/huntforge/output/test.com")
sh.record_end(sid, "COMPLETED", 5)
print(f"Inserted test scan id={sid}")
