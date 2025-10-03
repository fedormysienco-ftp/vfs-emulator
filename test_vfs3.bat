@echo off
cd /d "C:\Users\user\PycharmProjects\PythonProject1"
echo === Тест: Сложная VFS (3+ уровня) ===
start python konfig.py --vfs-path vfs_large.json --script test_vfs3.txt
pause