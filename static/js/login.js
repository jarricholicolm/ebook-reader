document.addEventListener('DOMContentLoaded', function () {
    // 密码显示切换
    const togglePassword = document.querySelector('.toggle-password');
    const passwordInput = document.querySelector('#password');

    if (togglePassword && passwordInput) {
        togglePassword.addEventListener('click', function () {
            const type = passwordInput.getAttribute('type') === 'password' ? 'text' : 'password';
            passwordInput.setAttribute('type', type);
            this.querySelector('i').classList.toggle('fa-eye');
            this.querySelector('i').classList.toggle('fa-eye-slash');
        });
    }

    // 表单提交处理
    const form = document.querySelector('.auth-form');
    const submitBtn = form.querySelector('.btn-primary');

    if (form) {  // 添加检查
        form.addEventListener('submit', async function (e) {
            e.preventDefault();
            if (submitBtn) {  // 添加检查
                submitBtn.classList.add('loading');
                submitBtn.disabled = true;
            }

            try {
                const response = await fetch('/api/login', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        username: document.getElementById('username').value,
                        password: document.getElementById('password').value
                    })
                });

                const data = await response.json();
                console.log('Login response:', data);  // 添加调试日志

                if (response.ok) {
                    // 保存访问令牌到localStorage
                    localStorage.setItem('access_token', data.access_token);
                    // 保存刷新令牌到localStorage
                    localStorage.setItem('refresh_token', data.refresh_token);  // 新增保存刷新令牌
                    // 设置访问令牌为cookie
                    document.cookie = `access_token_cookie=${data.access_token}; path=/`;
                    // 登录成功后跳转到首页
                    window.location.href = '/index';
                } else {
                    throw new Error(data.message || '登录失败');
                }
            } catch (error) {
                console.error('Login error:', error);  // 添加错误日志
                alert(error.message);
            } finally {
                if (submitBtn) {  // 添加检查
                    submitBtn.classList.remove('loading');
                    submitBtn.disabled = false;
                }
            }
        });
    }

    // 自动刷新令牌
    async function refreshAccessToken() {
        const refreshToken = localStorage.getItem('refresh_token'); // 获取刷新令牌
        if (!refreshToken) {
            console.error('没有找到刷新令牌，请重新登录');
            window.location.href = '/login';
            return;
        }

        try {
            const response = await fetch('/api/refresh', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${refreshToken}` // 在请求头中携带刷新令牌
                },
                credentials: 'include' // 确保发送cookie
            });

            if (!response.ok) {
                throw new Error('Token refresh failed');
            }

            const data = await response.json();
            localStorage.setItem('access_token', data.access_token); // 保存新的访问令牌
        } catch (error) {
            console.error('自动刷新令牌失败，请重新登录', error);
            window.location.href = '/login';
        }
    }

    // 定时器，定期刷新令牌
    setInterval(refreshAccessToken, 15 * 60 * 1000); // 每15分钟刷新一次
});
