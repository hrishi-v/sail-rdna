#pragma once

#define ASM_OUT(var) "=v"(var)
#define ASM_IN(var)  "v"(var)

#define STR_HELPER(x) #x
#define STR(x) STR_HELPER(x)