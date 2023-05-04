# JMX Tools

- Thay thế một số thuộc tính của file JMX.
- Chạy test (cần có Jmeter cài đặt).
- Chạy các tính năng trên theo batch.
- Sync input/output giữa các máy

## Sử dụng

### Cài đặt

```bash
pip install git+https://github.com/ndgnuh/jmx-tools.git
```

### Thay thế

Đầu vào/đầu ra:
```
# Chỉ định đầu vào/đầu ra
jmx-tools replace test.jmx -o test-replaced.jmx

# Thay thế trực tiếp file đầu vào
jmx-tools replace test.jmx

# Thay thế các file jmx trong thư mục
jmx-tools replace tests/
jmx-tools replace tests/ -o outputs/
```

Thay bearer (bearer không chứa chữ `Bearer ` ở đầu):
```bash
# Từ file
jmx-tools replace input.jmx -o output.jmx --bf bearer.txt

# Nhập tay
jmx-tools replace input.jmx -o output.jmx --bi "My token"
```

Thay CCU:
```bash
jmx-tools replace input.jmx -o output.jmx --ccu 100
```

Thay số vòng lặp mỗi threads:
```bash
jmx-tools replace input.jmx -o output.jmx --loops 1000
jmx-tools replace input.jmx -o output.jmx --loops -1 # Vô hạn
```

Thay lifetime của threads:
```bash
jmx-tools replace input.jmx -o output.jmx --duration 10s
jmx-tools replace input.jmx -o output.jmx --duration 10m
jmx-tools replace input.jmx -o output.jmx --duration 10:30 # 10 phút 30s
```

Thay tên của HTTP sampler để kết quả cuối hiển thị riêng từng endpoint:
```bash
jmx-tools replace input.jmx -o output.jmx --name2path
# prefix tên của sampler với method
jmx-tools replace input.jmx -o output.jmx --name2path --prefix-method
```
![](https://git.grooo.vn/ai/jbsv/jmeter-runner/-/raw/jmx-tools/images/summary.png)

Khớp endpoint jmx với endpoint của file postman (yêu cầu export ra file postman bản 2.1):
```shell
jmx-tools replace --mp postman.json input.jmx
```

Thay domain và protocol:
```bash
jmx-tools replace --domain localhost input.jmx
jmx-tools replace --protocol https input.jmx
```

### Chạy test

Nếu `jmeter` không nằm trên `PATH`:
```bash
export JMETER_PATH="/path/to/jmeter"
```

Chạy test thông thường:
```bash
jmx-tools run -i test.jmx -o test.csv
```

Chạy test có cài heap size, đơn vị là GB (mặc định của Jmeter là 1GB)
```bash
jmx-tools run -i test.jmx -o test.csv --heap 2
```

Chạy lại test, ghi đè kết quả:
```bash
jmx-tools run -i test.jmx -o test.csv -f
jmx-tools run -i test.jmx -o test.csv --force
```

Chạy toàn bộ test trong một thư mục (cả input và output phải là thư mục). Thứ tự chạy xác định bởi tên file.
```bash
jmx-tools run -i my-tests/ -o outputs/
# Đầu ra:
# - outputs/my-tests/test-1.csv
# - outputs/my-tests/test-2.csv
# - ...
```

### Sync

Gửi và nhận file `jmx` cũng như file kết quả nhanh hơn.

Máy gửi file:
```
# Tất cả file jmx trong thư mục hiện tại
jmx-tools push

# Tất cả file jmx trong thư mục input (sẽ tìm trong thư mục con)
jmx-tools push inputs/

# File tuỳ chọn
jmx-tools push test-1.jmx test-2.jmx
jmx-tools push inputs/*.jmx
jmx-tools push outputs/*.csv
```

Máy nhận file:
```shell
jmx-tools pull <ip máy gửi>
```

### Chạy batch

Thêm `batch` đằng trước lệnh (`replace`), dùng `,` để ngăn cách các tham số, dùng `{key}` để format đầu ra.

Lặp thay thế JMX:
```bash
mkdir tests -p
jmx-tools batch replace -i test.jmx -o tests/test-{ccu}.jmx --ccu 100,200,300
ls tests/ -l
# tests-100.jmx
# tests-200.jmx
# tests-300.jmx
```

Lặp chạy nhiều file test (Cần có dấu nháy đơn nếu không shell sẽ tự expand):
```bash
jmx-tools batch run -i 'tests/test-{100,200,300}.jmx' -o '{input}.csv'
# Sử dụng shell expand thay vì tính năng batch
jmx-tools run -i tests/test-{100,200,300}.jmx -o {100,200,300}.csv
```
