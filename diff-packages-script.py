def read_packages(filename):
    with open(filename, 'r') as f:
        return set(line.strip().lower().split('==')[0] for line in f if line.strip())


requirements = read_packages('requirements.txt')
installed = read_packages('installed_packages.txt')

to_uninstall = installed - requirements

with open('to_uninstall.txt', 'w') as f:
    for package in to_uninstall:
        f.write(f"{package}\n")

print(f"Found {len(to_uninstall)} packages to uninstall. Check 'to_uninstall.txt' for the list.")
