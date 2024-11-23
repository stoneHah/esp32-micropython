class RingBuffer:
    """环形缓冲区实现"""
    def __init__(self, size):
        self.size = size
        self.buffer = bytearray(size)
        self.write_pos = 0
        self.read_pos = 0
        self.available = 0
        
    def write(self, data):
        """写入数据到缓冲区"""
        # print(f"write:begin写入数据到缓冲区,可用大小: {self.available}")
        data_len = len(data)
        
        # 检查是否有足够的空间写入数据
        if data_len > self.size - self.available:
            print("write:缓冲区空间不足")
            return 0
        
        write_size = 0
            
        # 计算可写入长度
        if self.write_pos >= self.read_pos:
            # 写指针在读指针后面或相等
            # 可以写到缓冲区末尾，如果数据还有剩余且读指针不在开头，才能绕到开头继续写
            first_part = min(data_len, self.size - self.write_pos)
            # 写入第一部分
            self.buffer[self.write_pos:self.write_pos + first_part] = data[:first_part]
            write_size += first_part
            
            if first_part < data_len:
                # 还有数据需要写入，且必须确保不会覆盖到读指针
                if self.read_pos > 0:  # 只有读指针不在开头时才能写入第二部分
                    second_part = min(data_len - first_part, self.read_pos)
                    self.buffer[0:second_part] = data[first_part:first_part + second_part]
                    self.write_pos = second_part
                    write_size += second_part
                else:
                    # 读指针在开头，不能环绕写入
                    self.write_pos = 0
            else:
                self.write_pos = (self.write_pos + first_part) % self.size
        else:
            # 写指针在读指针前面，只能写到读指针位置
            first_part = min(data_len, self.read_pos - self.write_pos)
            self.buffer[self.write_pos:self.write_pos + first_part] = data[:first_part]
            self.write_pos += first_part
            write_size += first_part
            
        self.available += write_size
        # print(f"write:after写入数据后，缓冲区可用大小: {self.available}")
        return write_size
        
    def read(self, size):
        """从缓冲区读取数据"""
        # with self.lock:
        if self.available == 0:
            return bytearray(0)
            
        # print(f"read--begin:从缓冲区读取数据，可用大小: {self.available}")
        read_size = min(size, self.available)
        
        if self.read_pos < self.write_pos:
            # 读指针在写指针前面，最多只能读取到写指针位置
            first_part = min(read_size, self.write_pos - self.read_pos)
            result = bytearray(first_part)
            result = self.buffer[self.read_pos:self.read_pos + first_part]
            self.read_pos += first_part
            
            self.available -= first_part
            
        else:
            # 读指针在写指针后面或相等，需要考虑环绕读取
            first_part = min(read_size, self.size - self.read_pos)
            result = bytearray(read_size)
            result[:first_part] = self.buffer[self.read_pos:self.read_pos + first_part]
            
            if first_part < read_size:
                # 需要环绕读取
                # print(f"需要环绕读取")
                second_part = min(read_size - first_part, self.write_pos)
                result[first_part:] = self.buffer[0:second_part]
                self.read_pos = second_part
                
                self.available -= (first_part + second_part)
            else:
                # print(f"不需要环绕读取")
                self.read_pos = (self.read_pos + first_part) % self.size
                
                self.available -= first_part
                
        # print(f"read--after:从缓冲区读取数据，可用大小: {self.available}")
        return result