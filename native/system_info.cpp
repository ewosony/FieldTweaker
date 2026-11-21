// Optional native hardware diagnostics. No changes are made to the OS.
#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <iostream>
int main() {
    SYSTEM_INFO info{};
    GetNativeSystemInfo(&info);
    MEMORYSTATUSEX mem{}; mem.dwLength = sizeof(mem);
    if (!GlobalMemoryStatusEx(&mem)) return 1;
    std::cout << "{\"logical_processors\":" << info.dwNumberOfProcessors
              << ",\"ram_gb\":" << (mem.ullTotalPhys / (1024.0 * 1024 * 1024))
              << "}" << std::endl;
}
