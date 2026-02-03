async function fetchStats() {
    try {
        const response = await fetch('/api/stats/Brian_Sovereign');
        const data = await response.json();

        if (!data.error) {
            document.getElementById('stat-level').innerText = data.level;
            document.getElementById('stat-credits').innerText = data.credits.toLocaleString();

            const hours = Math.floor(data.total_time_wasted / 3600);
            const minutes = Math.floor((data.total_time_wasted % 3600) / 60);
            document.getElementById('stat-time').innerText = `${hours}h ${minutes}m`;
        }
    } catch (error) {
        console.error('Error fetching stats:', error);
    }
}

async function fetchLeaderboard() {
    try {
        const response = await fetch('/api/leaderboard');
        const data = await response.json();

        const tbody = document.querySelector('#leaderboard tbody');
        tbody.innerHTML = '';

        data.forEach((user, index) => {
            const row = document.createElement('tr');
            const hours = Math.floor(user.total_time_wasted / 3600);
            const minutes = Math.floor((user.total_time_wasted % 3600) / 60);

            row.innerHTML = `
                <td>#${index + 1}</td>
                <td>${user.user_id}</td>
                <td>Level ${user.level}</td>
                <td>${hours}h ${minutes}m</td>
            `;
            tbody.appendChild(row);
        });
    } catch (error) {
        console.error('Error fetching leaderboard:', error);
    }
}

// Initial fetch
fetchStats();
fetchLeaderboard();

// Refresh every 30 seconds
setInterval(() => {
    fetchStats();
    fetchLeaderboard();
}, 30000);
