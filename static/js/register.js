async function handleRegister(event) {
    event.preventDefault();
    const submitBtn = event.target.querySelector('.btn-primary');
    submitBtn.classList.add('loading');
    submitBtn.disabled = true;

    try {
        const formData = {
            username: document.getElementById('username').value,
            password: document.getElementById('password').value,
            email: document.getElementById('email').value
        };

        const response = await fetch('/api/register', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(formData)
        });

        const data = await response.json();

        if (response.ok) {
            // 注册成功，显示成功消息并跳转到登录页
            alert('注册成功！');
            window.location.href = '/login';
        } else {
            // 显示错误消息
            throw new Error(data.message || '注册失败');
        }
    } catch (error) {
        console.error('Registration error:', error);
        alert(error.message);
    } finally {
        submitBtn.classList.remove('loading');
        submitBtn.disabled = false;
    }
} 