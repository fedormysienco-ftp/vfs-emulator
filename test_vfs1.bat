@echo off
cd /d "C:\Users\user\PycharmProjects\PythonProject1"
echo === Тест: Минимальная VFS ===
start python konfig.py --vfs-path vfs_minimal.json --script test_vfs1.txt
pause