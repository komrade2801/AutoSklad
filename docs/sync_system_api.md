# API синхронизации AutoSklad

## Оглавление

1. [Общая информация](#общая-информация)
2. [Аутентификация и безопасность](#аутентификация-и-безопасность)
3. [Endpoints](#endpoints)
4. [Структуры данных](#структуры-данных)
5. [Коды ошибок](#коды-ошибок)
6. [Примеры запросов](#примеры-запросов)

---

## Общая информация

### Base URL

**Server**: `http://server_ip:8000`  
**Client**: `http://client_ip:8001`

### Content-Type

Все запросы и ответы используют:
- `Content-Type: application/octet-stream` (зашифрованные данные AES)
- После дешифрования: JSON

### Шифрование

Все тела запросов и ответов шифруются:
1. **AES-CBC** с 16-байтовым IV (Initialization Vector)
2. **HMAC-SHA256** для подписи
3. **JWT** для авторизации

---

## Аутентификация и безопасность

### JWT Token

Передается в заголовке:
```
Authorization: Bearer <jwt_token>
```

### HMAC Signature

Подпись вычисляется от зашифрованного тела:
```python
signature = hmac.new(
    key=hmac_secret,
    msg=encrypted_body,
    digestmod=hashlib.sha256
).hexdigest()
```

Передается в заголовке:
```
X-Signature: <hmac_hex>
```

### AES Encryption

**Алгоритм**: AES-CBC  
**Ключ**: 16/24/32 байта  
**IV**: 16 байт (случайный, в начале ciphertext)  

**Формат зашифрованных данных**:
```
[IV (16 байт)][Ciphertext (переменная длина)]
```

**Шифрование**:
```python
iv = os.urandom(16)
cipher = AES.new(aes_key, AES.MODE_CBC, iv)
padded = pad(json_bytes, AES.block_size)
ciphertext = cipher.encrypt(padded)
encrypted = iv + ciphertext
```

**Дешифрование**:
```python
iv = encrypted[:16]
ciphertext = encrypted[16:]
cipher = AES.new(aes_key, AES.MODE_CBC, iv)
padded = cipher.decrypt(ciphertext)
json_bytes = unpad(padded, AES.block_size)
```

---

## Endpoints

### 1. Handshake (Согласование схем)

#### POST /sync/handshake

Согласование схемы базы данных между клиентом и сервером.

**Query Parameters**:
- `device` (int, required) - ID устройства

**Request Body** (после дешифрования):
```json
{
  "schema": {
    "Tools": {
      "id": "integer",
      "name": "string",
      "count": "integer",
      "tool_type_id": "integer"
    },
    "Cell": {
      "id": "integer",
      "name": "string",
      "number_cell": "integer",
      "tools_id": "integer"
    }
  }
}
```

**Response** (после дешифрования):
```json
{
  "mapping": {
    "Tools": {
      "id": "index",
      "name": "name",
      "count": "count",
      "tool_type_id": "tool_type_id"
    },
    "Cell": {
      "id": "index",
      "name": "name",
      "number_cell": "number_cell",
      "tools_id": "tools_id"
    }
  },
  "schema_hash": "abc123def456..."
}
```

**Status Codes**:
- `200 OK` - Успешное согласование
- `400 Bad Request` - Невалидная схема
- `401 Unauthorized` - Неверный JWT токен
- `500 Internal Server Error` - Ошибка на сервере

**Пример cURL**:
```bash
# Подготовка данных
SCHEMA='{"schema":{"Tools":{"id":"integer","name":"string"}}}'
ENCRYPTED=$(python encrypt.py "$SCHEMA" "$AES_KEY")
SIGNATURE=$(python sign.py "$ENCRYPTED" "$HMAC_SECRET")

# Запрос
curl -X POST "http://server:8000/sync/handshake?device=1" \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "X-Signature: $SIGNATURE" \
  -H "Content-Type: application/octet-stream" \
  --data-binary "@$ENCRYPTED"
```

---

### 2. Push (Отправка локальных изменений)

#### POST /sync/push

Отправка локальных изменений на сервер.

**Query Parameters**:
- `device` (int, required) - ID устройства

**Request Body** (после дешифрования):
```json
{
  "device": 1,
  "schema_hash": "abc123def456...",
  "commands": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "table": "Tools",
      "operation": "INSERT",
      "data": {
        "index": 42,
        "name": "Отвертка",
        "count": 5,
        "tool_type_id": 1
      },
      "last_modified": ""
    },
    {
      "id": "660e8400-e29b-41d4-a716-446655440001",
      "table": "Cell",
      "operation": "UPDATE",
      "data": {
        "index": 10,
        "name": "Ячейка A1",
        "tools_id": 42
      },
      "last_modified": ""
    }
  ]
}
```

**Response** (после дешифрования):
```json
{
  "statuses": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "status": "COMPLETED"
    },
    {
      "id": "660e8400-e29b-41d4-a716-446655440001",
      "status": "COMPLETED"
    }
  ]
}
```

**Response (с ошибками)**:
```json
{
  "statuses": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "status": "COMPLETED"
    },
    {
      "id": "660e8400-e29b-41d4-a716-446655440001",
      "status": "FAILED",
      "error": "Validation failed: tools_id not found"
    }
  ]
}
```

**Status Codes**:
- `200 OK` - Команды обработаны (проверить статус каждой)
- `400 Bad Request` - Невалидный запрос
- `401 Unauthorized` - Неверный JWT токен
- `403 Forbidden` - Неверная HMAC подпись
- `409 Conflict` - Конфликт схем (нужен handshake)
- `500 Internal Server Error` - Ошибка на сервере

**Пример cURL**:
```bash
PAYLOAD='{
  "device": 1,
  "schema_hash": "abc123...",
  "commands": [...]
}'
ENCRYPTED=$(python encrypt.py "$PAYLOAD" "$AES_KEY")
SIGNATURE=$(python sign.py "$ENCRYPTED" "$HMAC_SECRET")

curl -X POST "http://server:8000/sync/push?device=1" \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "X-Signature: $SIGNATURE" \
  -H "Content-Type: application/octet-stream" \
  --data-binary "@$ENCRYPTED"
```

---

### 3. Pull (Получение удаленных изменений)

#### GET /sync/pull

Получение изменений с сервера.

**Query Parameters**:
- `device` (int, required) - ID устройства
- `since` (string, optional) - ISO 8601 timestamp, получить изменения после этой даты
- `schema_hash` (string, required) - Хэш схемы для валидации

**Response** (после дешифрования):
```json
{
  "schema_hash": "abc123def456...",
  "commands": [
    {
      "id": "15",
      "table": "Cell",
      "operation": "UPDATE",
      "data": {
        "index": 10,
        "name": "Ячейка A1",
        "number_cell": 1,
        "tools_id": 42
      },
      "last_modified": "2024-01-15T10:25:00.000Z"
    },
    {
      "id": "16",
      "table": "History",
      "operation": "INSERT",
      "data": {
        "index": 100,
        "user_id": 1,
        "tools_id": 42,
        "cell_id": 10,
        "datetime": "2024-01-15T10:25:00.000Z",
        "status": 2
      },
      "last_modified": "2024-01-15T10:25:30.000Z"
    }
  ]
}
```

**Response (нет изменений)**:
```json
{
  "schema_hash": "abc123def456...",
  "commands": []
}
```

**Status Codes**:
- `200 OK` - Успешно (даже если команд нет)
- `400 Bad Request` - Невалидные параметры
- `401 Unauthorized` - Неверный JWT токен
- `409 Conflict` - Конфликт схем (нужен handshake)
- `500 Internal Server Error` - Ошибка на сервере

**Пример cURL**:
```bash
SINCE="2024-01-15T10:00:00.000Z"
SCHEMA_HASH="abc123..."

# Формируем зашифрованный запрос (для GET это может быть просто query params)
curl -X GET "http://server:8000/sync/pull?device=1&since=$SINCE&schema_hash=$SCHEMA_HASH" \
  -H "Authorization: Bearer $JWT_TOKEN"
```

---

## Структуры данных

### Command (Команда синхронизации)

**Описание**: Представляет одну операцию изменения в базе данных.

```typescript
interface Command {
  id: string;              // UUID команды (client → server)
                           // или integer ID (server → client)
  table: string;           // Имя таблицы
  operation: "INSERT" | "UPDATE" | "DELETE";
  data: Record<string, any>;  // Полезная нагрузка
  last_modified?: string;  // ISO 8601 timestamp (UTC)
}
```

**Примеры**:

**INSERT**:
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "table": "Tools",
  "operation": "INSERT",
  "data": {
    "index": 42,
    "name": "Молоток",
    "count": 5,
    "tool_type_id": 1
  }
}
```

**UPDATE**:
```json
{
  "id": "660e8400-e29b-41d4-a716-446655440001",
  "table": "Cell",
  "operation": "UPDATE",
  "data": {
    "index": 10,
    "tools_id": 42
  }
}
```

**DELETE**:
```json
{
  "id": "770e8400-e29b-41d4-a716-446655440002",
  "table": "History",
  "operation": "DELETE",
  "data": {
    "index": 15
  }
}
```

### Schema (Схема базы данных)

**Описание**: Описание структуры таблиц и типов полей.

```typescript
interface Schema {
  [tableName: string]: {
    [fieldName: string]: string;  // Тип поля
  };
}
```

**Пример**:
```json
{
  "Tools": {
    "id": "integer",
    "name": "string",
    "count": "integer",
    "tool_type_id": "integer",
    "created_at": "datetime",
    "updated_at": "datetime"
  },
  "Cell": {
    "id": "integer",
    "name": "string",
    "number_cell": "integer",
    "tools_id": "integer"
  }
}
```

**Поддерживаемые типы**:
- `integer`
- `string` / `varchar`
- `float` / `double`
- `boolean`
- `datetime` / `timestamp`
- `date`
- `text`
- `json`

### Mapping (Маппинг полей)

**Описание**: Соответствие между полями клиента и сервера.

```typescript
interface Mapping {
  [tableName: string]: {
    [clientField: string]: string;  // serverField
  };
}
```

**Пример**:
```json
{
  "Tools": {
    "id": "index",
    "name": "name",
    "count": "quantity"
  },
  "Cell": {
    "id": "index",
    "name": "cell_name",
    "number_cell": "number"
  }
}
```

### CommandStatus (Статус команды)

**Описание**: Результат обработки команды.

```typescript
interface CommandStatus {
  id: string;           // ID команды
  status: "COMPLETED" | "FAILED";
  error?: string;       // Текст ошибки (если FAILED)
}
```

**Примеры**:

**Успех**:
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "COMPLETED"
}
```

**Ошибка**:
```json
{
  "id": "660e8400-e29b-41d4-a716-446655440001",
  "status": "FAILED",
  "error": "Validation failed: tools_id not found"
}
```

---

## Коды ошибок

### HTTP Status Codes

| Код | Название | Описание |
|-----|----------|----------|
| 200 | OK | Успешная обработка |
| 400 | Bad Request | Невалидный запрос (JSON, параметры) |
| 401 | Unauthorized | Неверный или отсутствующий JWT токен |
| 403 | Forbidden | Неверная HMAC подпись |
| 409 | Conflict | Конфликт схем (требуется handshake) |
| 500 | Internal Server Error | Ошибка на сервере |
| 503 | Service Unavailable | Сервер временно недоступен |

### Application Error Codes

В теле ответа при ошибках:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Validation failed for field 'count'",
    "details": {
      "field": "count",
      "value": -5,
      "constraint": "must be >= 0"
    }
  }
}
```

**Коды ошибок**:

| Код | Описание |
|-----|----------|
| `VALIDATION_ERROR` | Ошибка валидации данных |
| `SCHEMA_MISMATCH` | Несовпадение схем |
| `INTEGRITY_ERROR` | Нарушение целостности БД |
| `CONFLICT_ERROR` | Конфликт при одновременных изменениях |
| `NOT_FOUND` | Запись не найдена |
| `PERMISSION_DENIED` | Недостаточно прав |
| `TIMEOUT` | Превышено время ожидания |

---

## Примеры запросов

### Python (с использованием TransportService)

```python
from dbSync.Transport.TransportService import TransportService

# Инициализация
transport = TransportService(
    base_url="http://server:8000",
    jwt_token="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    hmac_secret=b"supersecret",
    aes_key=b"16byteslongkey!!",
    device_id=1,
    Port="8000"
)

# 1. Handshake
client_schema = {
    "Tools": {
        "id": "integer",
        "name": "string",
        "count": "integer"
    }
}

response = transport.send_schema("/sync/handshake", client_schema, device=1)
mapping = response["mapping"]
schema_hash = response["schema_hash"]

print(f"Schema hash: {schema_hash}")
print(f"Mapping: {mapping}")

# 2. Push
payload = {
    "device": 1,
    "schema_hash": schema_hash,
    "commands": [
        {
            "id": "550e8400-e29b-41d4-a716-446655440000",
            "table": "Tools",
            "operation": "INSERT",
            "data": {
                "index": 42,
                "name": "Молоток",
                "count": 5
            }
        }
    ]
}

response = transport.send_push("/sync/push", payload)
statuses = response["statuses"]

for status in statuses:
    print(f"Command {status['id']}: {status['status']}")
    if status['status'] == 'FAILED':
        print(f"  Error: {status.get('error')}")

# 3. Pull
params = {
    "device": 1,
    "since": "2024-01-15T10:00:00.000Z",
    "schema_hash": schema_hash
}

response = transport.send_pull("/sync/pull", params)
commands = response["commands"]

print(f"Received {len(commands)} commands")
for cmd in commands:
    print(f"  {cmd['table']}.{cmd['operation']}: {cmd['data']}")
```

### JavaScript (Node.js)

```javascript
const crypto = require('crypto');
const axios = require('axios');

class TransportService {
  constructor(baseUrl, jwtToken, hmacSecret, aesKey) {
    this.baseUrl = baseUrl;
    this.jwtToken = jwtToken;
    this.hmacSecret = Buffer.from(hmacSecret);
    this.aesKey = Buffer.from(aesKey);
  }

  encrypt(data) {
    const json = JSON.stringify(data);
    const iv = crypto.randomBytes(16);
    const cipher = crypto.createCipheriv('aes-128-cbc', this.aesKey, iv);
    
    let encrypted = cipher.update(json, 'utf8', 'binary');
    encrypted += cipher.final('binary');
    
    return Buffer.concat([iv, Buffer.from(encrypted, 'binary')]);
  }

  decrypt(encrypted) {
    const iv = encrypted.slice(0, 16);
    const ciphertext = encrypted.slice(16);
    
    const decipher = crypto.createDecipheriv('aes-128-cbc', this.aesKey, iv);
    
    let decrypted = decipher.update(ciphertext, 'binary', 'utf8');
    decrypted += decipher.final('utf8');
    
    return JSON.parse(decrypted);
  }

  sign(data) {
    return crypto
      .createHmac('sha256', this.hmacSecret)
      .update(data)
      .digest('hex');
  }

  async sendPush(endpoint, payload) {
    const encrypted = this.encrypt(payload);
    const signature = this.sign(encrypted);
    
    const response = await axios.post(
      `${this.baseUrl}${endpoint}?device=${payload.device}`,
      encrypted,
      {
        headers: {
          'Authorization': `Bearer ${this.jwtToken}`,
          'X-Signature': signature,
          'Content-Type': 'application/octet-stream'
        },
        responseType: 'arraybuffer'
      }
    );
    
    return this.decrypt(Buffer.from(response.data));
  }

  async sendPull(endpoint, params) {
    const url = `${this.baseUrl}${endpoint}?` + 
      new URLSearchParams(params).toString();
    
    const response = await axios.get(url, {
      headers: {
        'Authorization': `Bearer ${this.jwtToken}`
      },
      responseType: 'arraybuffer'
    });
    
    return this.decrypt(Buffer.from(response.data));
  }
}

// Использование
const transport = new TransportService(
  'http://server:8000',
  'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...',
  'supersecret',
  '16byteslongkey!!'
);

// Push
const payload = {
  device: 1,
  schema_hash: 'abc123...',
  commands: [
    {
      id: '550e8400-e29b-41d4-a716-446655440000',
      table: 'Tools',
      operation: 'INSERT',
      data: {
        index: 42,
        name: 'Молоток',
        count: 5
      }
    }
  ]
};

transport.sendPush('/sync/push', payload)
  .then(response => {
    console.log('Statuses:', response.statuses);
  })
  .catch(error => {
    console.error('Error:', error.message);
  });

// Pull
const params = {
  device: 1,
  since: '2024-01-15T10:00:00.000Z',
  schema_hash: 'abc123...'
};

transport.sendPull('/sync/pull', params)
  .then(response => {
    console.log(`Received ${response.commands.length} commands`);
    response.commands.forEach(cmd => {
      console.log(`  ${cmd.table}.${cmd.operation}:`, cmd.data);
    });
  })
  .catch(error => {
    console.error('Error:', error.message);
  });
```

### cURL с шифрованием (bash скрипт)

```bash
#!/bin/bash

# encrypt.sh - Скрипт для шифрования и отправки запросов

AES_KEY="16byteslongkey!!"
HMAC_SECRET="supersecret"
JWT_TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
SERVER="http://server:8000"

# Функция шифрования (требует Python)
encrypt() {
    local data="$1"
    python3 -c "
import os
import json
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad

aes_key = b'$AES_KEY'
data = b'$data'

iv = os.urandom(16)
cipher = AES.new(aes_key, AES.MODE_CBC, iv)
padded = pad(data, AES.block_size)
ciphertext = cipher.encrypt(padded)

import sys
sys.stdout.buffer.write(iv + ciphertext)
"
}

# Функция подписи
sign() {
    local data="$1"
    echo -n "$data" | openssl dgst -sha256 -hmac "$HMAC_SECRET" | awk '{print $2}'
}

# Push запрос
push() {
    local payload='{
      "device": 1,
      "schema_hash": "abc123...",
      "commands": [{
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "table": "Tools",
        "operation": "INSERT",
        "data": {"index": 42, "name": "Молоток", "count": 5}
      }]
    }'
    
    local encrypted=$(encrypt "$payload")
    local signature=$(sign "$encrypted")
    
    curl -X POST "$SERVER/sync/push?device=1" \
      -H "Authorization: Bearer $JWT_TOKEN" \
      -H "X-Signature: $signature" \
      -H "Content-Type: application/octet-stream" \
      --data-binary "$encrypted"
}

# Pull запрос
pull() {
    local since="2024-01-15T10:00:00.000Z"
    local schema_hash="abc123..."
    
    curl -X GET "$SERVER/sync/pull?device=1&since=$since&schema_hash=$schema_hash" \
      -H "Authorization: Bearer $JWT_TOKEN"
}

# Вызов функций
push
pull
```

---

## WebSocket API (опционально)

### Подключение

```javascript
const ws = new WebSocket('ws://server:8000/sync/ws?device=1');

ws.onopen = () => {
  console.log('Connected to sync server');
  
  // Отправка handshake
  ws.send(JSON.stringify({
    type: 'handshake',
    schema: { /* схема */ }
  }));
};

ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  
  switch(message.type) {
    case 'handshake_response':
      console.log('Mapping:', message.mapping);
      break;
    
    case 'push':
      // Получена команда от сервера
      console.log('Command:', message.command);
      applyCommand(message.command);
      
      // Подтверждение
      ws.send(JSON.stringify({
        type: 'ack',
        command_id: message.command.id
      }));
      break;
    
    case 'ack':
      // Сервер подтвердил нашу команду
      console.log('Command acknowledged:', message.command_id);
      break;
  }
};

// Отправка команды
function sendCommand(command) {
  ws.send(JSON.stringify({
    type: 'push',
    command: command
  }));
}
```

---

## Заключение

Этот API обеспечивает:

✅ Безопасную передачу данных (AES + HMAC + JWT)  
✅ Согласование схем (handshake)  
✅ Двустороннюю синхронизацию (push/pull)  
✅ Детальные статусы команд  
✅ Обработку ошибок  
✅ Масштабируемость (WebSocket для real-time)  

Для production рекомендуется:
- Использовать HTTPS вместо HTTP
- Регулярно обновлять JWT токены
- Мониторить метрики API (latency, errors)
- Настроить rate limiting
- Использовать compression (gzip) для больших payload



