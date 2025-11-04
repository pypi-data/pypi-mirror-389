# Changelog

## [2.0.1] - 2025-11-03
    add pygments>=2.7.4

## [2.0.0] - 2025-10-31
    python >=3.13
    certifi>=2024.2.2
    requests[security]>=2.32.4
    urllib3>=2.5.0
    uwsgi>=2.0.21 ; sys_platform != 'win32'
    zipp>=3.19.1

## [1.0.2] - 2024-10-01 
    - zipp>=3.19.1
    - requests>=2.32.0
    - setup python@v5
    - codecov token
    - graalpy and jupyter is not supported because of uwsgi pinning

## [1.0.1] - 2024-10-01
    - do not import uwsgi on windows and platform implementations other then cpython, for graalpy 24.1 and jupyter
    - zipp>=3.19.1
    - requests>=2.32.0
    - add graalpy tests
    - setup python@v5
    - codecov token

## [1.0.0] - 2024-03-01 
    Initial release
    certifi>=2024.2.2  # pinned to avoid vulnerability CVE-2023-37920
    pip>=24.0          # pinned to avoid vulnerability CVE-2023-5752
    uwsgi>=2.0.21; sys_platform != 'win32'  # pinned to avoid vulnerability CVE-2023-27522
    urllib3>=2.2.0     # pinned to avoid vulnerability CVE-2023-43804, CVE-2023-45803
