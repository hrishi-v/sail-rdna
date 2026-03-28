#pragma once
#include <iostream>
#include <string>

inline void log_info(const std::string& tag, const std::string& msg) {
    std::cout << "[" << tag << "] " << msg << "\n";
}

inline void log_warn(const std::string& tag, const std::string& msg) {
    std::cout << "[" << tag << " WARN] " << msg << "\n";
}

inline void log_error(const std::string& tag, const std::string& msg) {
    std::cerr << "[" << tag << " ERROR] " << msg << "\n";
}
