## Rule LGEDV_CRCL_0001:
Definition: Always use named constants or enumerations instead of hard-coded numeric values (magic numbers) in the code.

Example violation:
```cpp
int timeout = 30; // Violation: magic number
```
Compliant example:
```cpp
const int TIMEOUT_SECONDS = 30;
int timeout = TIMEOUT_SECONDS;
```

## Rule LGEDV_CRCL_0002:
Definition: Eliminate duplicate code by creating shared classes or functions for similar operations.

Example violation:
```cpp
void logInfo(const std::string& msg) { std::cout << msg << std::endl; }
void logError(const std::string& msg) { std::cerr << msg << std::endl; }
```
Compliant example:
```cpp
void log(const std::string& msg, std::ostream& out) { out << msg << std::endl; }
```

## Rule LGEDV_CRCL_0003:
Definition: Only allow early return statements for guard clauses (such as input validation) at the start of a function. The main logic of the function must have only one return statement at the end.

Example violation:
```cpp
int foo(int x) {
    if (x < 0) return -1;
    if (x == 0) return 0;
    return x * 2;
}
```
Compliant example:
```cpp
int foo(int x) {
    if (x < 0) return -1;
    int result;
    if (x == 0)
        result = 0;
    else
        result = x * 2;
    return result;
}
```

## Rule LGEDV_CRCL_0004:
Definition: Initialize return values to an error or failure state (e.g., negative, false, or FAILED) by default.

Example violation:
```cpp
int result;
if (success) result = 1;
```
Compliant example:
```cpp
int result = -1;
if (success) result = 1;
```

<!-- ## Rule LGEDV_CRCL_0008:
All log statements must use a common utility function to ensure a consistent log format throughout the codebase. Do not use custom or ad-hoc logging formats. -->

## Rule LGEDV_CRCL_0009:
Definition: Functions should have a cyclomatic complexity less than 10. Refactor complex functions for better readability and maintainability.

Example violation:
```cpp
void process(int x) {
    if (x > 0) { /* ... */ }
    else if (x == 0) { /* ... */ }
    else if (x < 0) { /* ... */ }
    // ... many more branches ...
}
```
Compliant example:
```cpp
void processPositive(int x) { /* ... */ }
void processZero() { /* ... */ }
void processNegative(int x) { /* ... */ }

void process(int x) {
    if (x > 0) processPositive(x);
    else if (x == 0) processZero();
    else processNegative(x);
}
```

<!-- ## Rule LGEDV_CRCL_0010:
Definition: Return values must be meaningful. Avoid returning only a boolean (e.g., just True). Change the return type if a simple boolean is not sufficient. -->

<!-- ## Rule LGEDV_CRCL_0011:
Definition: Add a log statement at the start of each function, especially for public interfaces. Log important information for decision branches. -->

## Rule LGEDV_CRCL_0012:
Definition: Ensure file data is synchronized to disk after modifications by calling sync after flush or close, considering performance impact.

Example violation:
```cpp
file.close(); // No sync
```
Compliant example:
```cpp
file.flush();
fsync(fileDescriptor);
file.close();
```

## Rule LGEDV_CRCL_0013:
Definition: Every case in a switch statement must end with a break statement unless intentional fall-through is clearly documented.

Example violation:
```cpp
switch (x) {
    case 1:
        doSomething();
    case 2:
        doSomethingElse();
        break;
}
```
Compliant example:
```cpp
switch (x) {
    case 1:
        doSomething();
        break;
    case 2:
        doSomethingElse();
        break;
}
```

## Rule LGEDV_CRCL_0014:
Definition: Always check pointer parameters for null before use, and validate array or vector indices to prevent out-of-bounds access.

Example violation:
```cpp
void foo(int* ptr) {
    *ptr = 10; // No null check
}
```
Compliant example:
```cpp
void foo(int* ptr) {
    if (ptr) *ptr = 10;
}
```

## Rule LGEDV_CRCL_0015:
Definition: If a switch case contains two or more statements, enclose them in curly braces to form a code block.

Example violation:
```cpp
switch (x) {
    case 1:
        doA();
        doB();
        break;
}
```
Compliant example:
```cpp
switch (x) {
    case 1: {
        doA();
        doB();
        break;
    }
}
```

## Rule LGEDV_CRCL_0016:
Definition: Use bounded C functions (e.g., snprintf instead of sprintf) to prevent buffer overflows.

Example violation:
```cpp
char buf[10];
sprintf(buf, "%s", input); // Unsafe
```
Compliant example:
```cpp
char buf[10];
snprintf(buf, sizeof(buf), "%s", input); // Safe
```

<!-- ## Rule LGEDV_CRCL_0018:
Definition: Avoid naming conflicts between classes or constants in libraries and applications by using unique names or namespaces. -->

<!-- ## Rule LGEDV_CRCL_0019:
Definition: Every function should return a meaningful value. Reconsider the use of void return types; use them only when no return value is necessary. -->

## Rule LGEDV_CRCL_0020:
Definition: Release all allocated resources (memory, files, mutexes, etc.) before exiting a function to prevent resource leaks.

Example violation:
```cpp
void foo() {
    int* p = new int[10];
    // ... use p ...
    // forgot: delete[] p;
}
```
Compliant example:
```cpp
void foo() {
    int* p = new int[10];
    // ... use p ...
    delete[] p;
}
```

## Rule LGEDV_CRCL_0021:
Definition: All functions that may throw exceptions or encounter errors must implement sufficient exception handling and error recovery logic. Catch exceptions at appropriate levels and ensure the system can recover or fail gracefully.

Example violation:
```cpp
void foo() {
    riskyOperation(); // No try-catch
}
```
Compliant example:
```cpp
void foo() {
    try {
        riskyOperation();
    } catch (const std::exception& e) {
        // Handle error or recover
    }
}
```

## Rule LGEDV_CRCL_0022:
Definition: For every critical operation (e.g., file I/O, memory allocation, communication), check the return value or error code, and handle all error cases explicitly. Do not ignore potential failures.

Example violation:
```cpp
fopen("file.txt", "r"); // Ignoring return value
```
Compliant example:
```cpp
FILE* f = fopen("file.txt", "r");
if (!f) {
    // Handle error
}
```

## Rule LGEDV_CRCL_0023:
Definition: Always validate that variable values do not exceed the allowed size of their data types to prevent overflow or underflow. Perform explicit checks before assignments, arithmetic operations, or when receiving external input.

Example violation:
```cpp
uint8_t a = 300; // Violation: 300 exceeds the maximum value of uint8_t (255)
int16_t b = a * 10000; // Possible overflow if not checked
```
Compliant example:
```cpp
uint8_t a = (input > 255) ? 255 : input; // Ensure value does not exceed type size
int16_t b;
if (a <= INT16_MAX / 10000) {
    b = a * 10000;
} else {
    // Handle overflow error
}
```