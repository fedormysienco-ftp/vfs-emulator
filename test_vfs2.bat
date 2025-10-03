@echo off
cd /d "C:\Users\user\PycharmProjects\PythonProject1"
echo === Тест: Средняя VFS ===
start python konfig.py --vfs-path vfs_medium.json --script test_vfs2.txt
pause