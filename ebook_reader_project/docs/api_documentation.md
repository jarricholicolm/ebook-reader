## **eBook Reader API 文档**

### **1. 用户注册接口**
**`POST /register`**

**请求参数（JSON）**：
```json
{
    "username": "string", 
    "email": "string",     
    "password": "string"   
}
```

**响应**：
- 成功（201 Created）：
  ```json
  {
      "message": "User created successfully!"
  }
  ```
- 失败（401 Unauthorized）：
  ```json
  {
      "message": "Duplicate username, please re-enter username!"
  }
  ```

---

### **2. 用户登录接口**
**`POST /login`**

**请求参数（JSON）**：
```json
{
    "username": "string",  
    "password": "string"   
}
```

**响应**：
- 成功（200 OK）：
  ```json
  {
      "access_token": "string"  
  }
  ```
- 失败（401 Unauthorized）：
  ```json
  {
      "message": "Invalid credentials"
  }
  ```

---

### **3. 用户个人页面接口**
**`GET /profile`**
> 需要提供有效的 JWT token

**响应**：
- 成功（200 OK）：
  ```json
  {
      "message": "hello, {username}! This is your profile."
  }
  ```

---

### **4. 上传书籍接口**
**`POST /upload_book`**

**请求参数**：
- 文件（`file`）：电子书文件（支持 `.pdf`, `.epub` 格式）
- 其他表单参数：
  - `title`：书籍标题
  - `author`：书籍作者
  - `description`：书籍描述

**响应**：
- 成功（201 Created）：
  ```json
  {
      "message": "Book uploaded successfully!"
  }
  ```
- 失败（400 Bad Request）：
  ```json
  {
      "message": "Invalid file format"
  }
  ```

---

### **5. 下载书籍接口**
**`GET /download_book/<int:book_id>`**

**URL 参数**：
- `book_id`：书籍的 ID（整数）

**响应**：
- 成功（200 OK）：返回书籍文件
- 失败（404 Not Found）：
  ```json
  {
      "message": "Book not found"
  }
  ```

---

### **6. 获取书籍列表接口**
**`GET /books`**

**响应**：
- 成功（200 OK）：
  ```json
  [
      {
          "id": "integer",       
          "title": "string",      
          "author": "string",     
          "cover_url": "string"   
      }
  ]
  ```

---

### **7. 更新阅读进度接口**
**`POST /update_progress`**
> 需要提供有效的 JWT token

**请求参数（JSON）**：
```json
{
    "book_id": "integer",      
    "progress": "float",      
    "current_page": "integer"  
}
```

**响应**：
- 成功（200 OK）：
  ```json
  {
      "message": "Reading progress updated successfully!"
  }
  ```
- 失败（400 Bad Request）：
  ```json
  {
      "message": "Missing required fields!"
  }
  ```

---

### **8. 获取用户阅读历史接口**
**`GET /reading_history`**
> 需要提供有效的 JWT token

**响应**：
- 成功（200 OK）：
  ```json
  {
      "reading_history": [
          {
              "book_id": "integer",    
              "title": "string",       
              "author": "string",      
              "progress": "float",     
              "current_page": "integer" 
          }
      ]
  }
  ```

---

### **9. 首页路由**
**`GET /`**

**响应**：
- 成功（200 OK）：
  ```json
  {
      "message": "Welcome to the eBook Reader App!"
  }
  ```

---

## **认证与授权**

所有需要用户身份验证的接口（如 `/profile`, `/update_progress`, `/reading_history`）都需要提供 **JWT token** 作为请求头中的 `Authorization` 字段。

**请求示例**：
```http
GET /profile HTTP/1.1
Authorization: Bearer <your_jwt_token>
```

---

## **常见错误代码**

- **400 Bad Request**：请求格式不正确或缺少必需的字段。
- **401 Unauthorized**：用户未提供有效的身份凭证或无权访问资源。
- **404 Not Found**：请求的资源未找到。
- **500 Internal Server Error**：服务器内部错误，通常是程序代码或数据库操作问题。

---