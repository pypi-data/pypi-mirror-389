$(document).ready(function() {
    let currentSection = 'overview';
    let currentSeverityFilter = 'all';
    let refreshInterval;
    const REFRESH_INTERVAL = 60000; // 60 seconds (reduced from 30)
    let isLoading = false; // Prevent multiple simultaneous requests

    // Global AJAX error handler for unauthorized requests
    $(document).ajaxError(function(event, jqXHR, ajaxSettings, thrownError) {
        if (jqXHR.status === 401) {
            console.log('🔒 Session expired, redirecting to login...');
            window.location.href = '/perfwatch/dashboard/';
        }
    });

    // Initialize
    setupEventListeners();
    
    // Set Overview section as active by default
    $('a[href="#overview"]').addClass('active bg-gray-700');
    
    // Set "All APIs" filter as active by default
    $('.severity-filter[data-severity="all"]').addClass('bg-gray-700');
    
    // Start auto-refresh
    startAutoRefresh();
    
    // Load dashboard data immediately on page load
    setTimeout(() => {
        loadDashboardData();
    }, 100);

    function setupEventListeners() {
        // Sidebar toggle
        $('#sidebar-toggle').click(function() {
            $('#sidebar').toggleClass('-translate-x-full');
        });

        // Section navigation
        $('.sidebar-link').click(function(e) {
            e.preventDefault();
            showLoadingOverlay('Loading section...');
            const section = $(this).attr('href').substring(1);
            switchSection(section);
            setTimeout(hideLoadingOverlay, 500);
        });

        // Severity filters
        $('.severity-filter').click(function() {
            showLoadingOverlay('Filtering data...');
            $('.severity-filter').removeClass('bg-gray-700');
            $(this).addClass('bg-gray-700');
            currentSeverityFilter = $(this).data('severity');
            currentPage = 1;  // Reset to first page when filter changes
            loadDashboardData().finally(hideLoadingOverlay);
        });

        // Time filter
        $('#time-filter').change(function() {
            const selectedValue = $(this).val();
            
            if (selectedValue === 'custom') {
                // Show custom date range inputs
                $('#custom-date-range').show();
                
                // Set default dates (last 7 days to now)
                const now = new Date();
                const weekAgo = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
                
                $('#end-date').val(formatDateTimeLocal(now));
                $('#start-date').val(formatDateTimeLocal(weekAgo));
            } else {
                // Hide custom date range inputs and load data immediately
                $('#custom-date-range').hide();
                showLoadingOverlay('Loading data...');
                currentPage = 1;
                loadDashboardData().finally(hideLoadingOverlay);
            }
        });
        
        // Apply custom date range button
        $('#apply-custom-date').click(function() {
            const startDate = $('#start-date').val();
            const endDate = $('#end-date').val();
            
            // Validate dates
            if (!startDate || !endDate) {
                alert('Please select both start and end dates');
                return;
            }
            
            const start = new Date(startDate);
            const end = new Date(endDate);
            
            if (start >= end) {
                alert('Start date must be before end date');
                return;
            }
            
            if (end > new Date()) {
                alert('End date cannot be in the future');
                return;
            }
            
            // Check if range is more than 1 year
            const oneYearMs = 365 * 24 * 60 * 60 * 1000;
            if (end - start > oneYearMs) {
                alert('Date range cannot exceed 1 year');
                return;
            }
            
            // Load data with custom date range
            showLoadingOverlay('Loading data...');
            currentPage = 1;
            loadDashboardData().finally(hideLoadingOverlay);
        });
        
        // Helper function to format date for datetime-local input
        function formatDateTimeLocal(date) {
            const year = date.getFullYear();
            const month = String(date.getMonth() + 1).padStart(2, '0');
            const day = String(date.getDate()).padStart(2, '0');
            const hours = String(date.getHours()).padStart(2, '0');
            const minutes = String(date.getMinutes()).padStart(2, '0');
            return `${year}-${month}-${day}T${hours}:${minutes}`;
        }

        // Search button click handler
        $('#search-button').click(function() {
            showLoadingOverlay('Searching...');
            loadHistoryData().finally(hideLoadingOverlay);
        });

        // Also allow search on Enter key
        $('#endpoint-search').keypress(function(e) {
            if (e.which === 13) { // Enter key
                showLoadingOverlay('Searching...');
                loadHistoryData().finally(hideLoadingOverlay);
            }
        });

        // Manual refresh
        $('#refresh-now').click(function() {
            $(this).addClass('animate-spin');
            loadDashboardData().finally(() => {
                $(this).removeClass('animate-spin');
            });
        });

        // Modal close
        $('.modal-close').click(closeModal);
        
        // Tree drawer close
        $('.tree-drawer-close').click(closeTreeDrawer);
        $('#tree-drawer').click(function(e) {
            if (e.target.id === 'tree-drawer') {
                closeTreeDrawer();
            }
        });
        
        // Analysis modal close
        $('#analysis-modal').click(function(e) {
            if (e.target.id === 'analysis-modal') {
                closeAnalysisModal();
            }
        });
        
        // Memory modal close
        $('#memory-modal').click(function(e) {
            if (e.target.id === 'memory-modal') {
                closeMemoryDrawer();
            }
        });
        
        // Profiling toggle
        $('#profiling-toggle').click(function() {
            toggleProfiling();
        });
        
        // Load profiling status on page load
        loadProfilingStatus();
    }

    function startAutoRefresh() {
        updateRefreshStatus();
        refreshInterval = setInterval(() => {
            loadDashboardData();
            updateRefreshStatus();
        }, REFRESH_INTERVAL);
    }

    function updateRefreshStatus() {
        const now = new Date();
        $('#refresh-status').text(`Last updated: ${now.toLocaleTimeString()}`);
    }

    function switchSection(section) {
        currentSection = section;
        // Remove active class from all links
        $('.sidebar-link').removeClass('active bg-gray-700');
        // Add active class to current section link
        $(`a[href="#${section}"]`).addClass('active bg-gray-700');
        
        // Hide all sections
        $('#overview-section, #history-section').addClass('hidden');
        // Show current section
        $(`#${section}-section`).removeClass('hidden');

        if (section === 'history') {
            loadHistoryData();
        }
    }

    // Pagination state
    let currentPage = 1;
    let pageSize = 10;
    let totalPages = 1;

    async function loadDashboardData() {
        // Prevent multiple simultaneous requests
        if (isLoading) {
            console.log('⏳ Already loading, skipping...');
            return;
        }
        
        isLoading = true;
        $('#refresh-now').addClass('opacity-50 cursor-not-allowed');
        
        try {
            const timeFilter = $('#time-filter').val();
            const params = {
                timeframe: timeFilter,
                severity: currentSeverityFilter,
                page: currentPage,
                page_size: pageSize
            };
            
            // Add custom date range if selected
            if (timeFilter === 'custom') {
                const startDate = $('#start-date').val();
                const endDate = $('#end-date').val();
                
                if (startDate && endDate) {
                    params.start_date = startDate;
                    params.end_date = endDate;
                }
            }
            
            const response = await $.get('/perfwatch/api/stats', params);
            
            updateDashboard(response);
            if (currentSection === 'overview') {
                updateAPIList(response.heaviest_apis || []);
                if (response.pagination) {
                    updatePagination(response.pagination);
                }
            }
        } catch (error) {
            console.error('Error loading dashboard data:', error);
            if (error.status === 401) {
                window.location.href = '/perfwatch/dashboard/';
            }
        } finally {
            isLoading = false;
            $('#refresh-now').removeClass('opacity-50 cursor-not-allowed');
        }
    }

    function updatePagination(pagination) {
        totalPages = pagination.total_pages;
        const paginationHtml = `
            <div class="flex items-center justify-between mt-4 px-4">
                <div class="text-sm text-gray-400">
                    Showing ${((pagination.page - 1) * pagination.page_size) + 1} to 
                    ${Math.min(pagination.page * pagination.page_size, pagination.total_count)} 
                    of ${pagination.total_count} APIs
                </div>
                <div class="flex items-center space-x-2">
                    <button 
                        class="px-3 py-1 rounded ${pagination.has_prev ? 'bg-blue-600 hover:bg-blue-700 text-white' : 'bg-gray-700 text-gray-500 cursor-not-allowed'}" 
                        onclick="changePage(${pagination.page - 1})"
                        ${!pagination.has_prev ? 'disabled' : ''}>
                        <i class="fas fa-chevron-left"></i> Previous
                    </button>
                    
                    <div class="flex space-x-1">
                        ${generatePageNumbers(pagination.page, pagination.total_pages)}
                    </div>
                    
                    <button 
                        class="px-3 py-1 rounded ${pagination.has_next ? 'bg-blue-600 hover:bg-blue-700 text-white' : 'bg-gray-700 text-gray-500 cursor-not-allowed'}" 
                        onclick="changePage(${pagination.page + 1})"
                        ${!pagination.has_next ? 'disabled' : ''}>
                        Next <i class="fas fa-chevron-right"></i>
                    </button>
                </div>
            </div>
        `;
        $('#pagination-container').html(paginationHtml);
    }

    function generatePageNumbers(currentPage, totalPages) {
        let pages = [];
        const maxVisible = 5;
        
        if (totalPages <= maxVisible) {
            for (let i = 1; i <= totalPages; i++) {
                pages.push(i);
            }
        } else {
            if (currentPage <= 3) {
                pages = [1, 2, 3, 4, '...', totalPages];
            } else if (currentPage >= totalPages - 2) {
                pages = [1, '...', totalPages - 3, totalPages - 2, totalPages - 1, totalPages];
            } else {
                pages = [1, '...', currentPage - 1, currentPage, currentPage + 1, '...', totalPages];
            }
        }
        
        return pages.map(page => {
            if (page === '...') {
                return '<span class="px-2 text-gray-500">...</span>';
            }
            const isActive = page === currentPage;
            return `
                <button 
                    class="px-3 py-1 rounded ${isActive ? 'bg-blue-600 text-white' : 'bg-gray-700 text-gray-300 hover:bg-gray-600'}"
                    onclick="changePage(${page})">
                    ${page}
                </button>
            `;
        }).join('');
    }

    window.changePage = function(page) {
        if (page < 1 || page > totalPages) return;
        currentPage = page;
        loadDashboardData();
    };

    window.changePageSize = function(size) {
        pageSize = size;
        currentPage = 1;  // Reset to first page
        loadDashboardData();
    };

    function updateDashboard(data) {
        // Update counters and percentages
        const total = data.counts.total || 0;
        updateCounter('critical', data.counts.critical, total);
        updateCounter('warning', data.counts.warning, total);
        updateCounter('normal', data.counts.normal, total);
        $('#total-count').text(total.toLocaleString());
    }

    function updateCounter(type, count, total) {
        $(`#${type}-count`).text(count.toLocaleString());
        const percent = total > 0 ? ((count / total) * 100).toFixed(1) : 0;
        $(`#${type}-percent`).text(`${percent}% of total`);
    }

    function updateAPIList(apis) {
        // Don't filter here - backend already handles filtering and pagination
        const html = apis.map(api => `
            <tr class="border-b border-gray-700">
                <td class="px-6 py-4 font-mono">${api.endpoint}</td>
                <td class="px-6 py-4">${api.method}</td>
                <td class="px-6 py-4">${formatDuration(api.total_time)}</td>
                <td class="px-6 py-4">${api.query_count}</td>
                <td class="px-6 py-4">${formatTimestamp(api.last_called)}</td>
                <td class="px-6 py-4">${getSeverityBadge(api.severity)}</td>
                <td class="px-6 py-4">
                    <div class="flex space-x-2">
                        <button class="px-2 py-0.5 text-white text-xs rounded font-semibold shadow-lg transition-all duration-200 hover:shadow-xl hover:scale-105" 
                                style="background: linear-gradient(135deg, #a855f7 0%, #9333ea 100%); box-shadow: 0 4px 12px rgba(168, 85, 247, 0.4);"
                                onclick="showMemoryMetrics('${api.id}')">
                            <i class="fas fa-memory mr-1"></i>Memory
                        </button>
                        <button class="px-2 py-0.5 text-white text-xs rounded font-semibold shadow-lg transition-all duration-200 hover:shadow-xl hover:scale-105" 
                                style="background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%); box-shadow: 0 4px 12px rgba(59, 130, 246, 0.4);"
                                onclick="showApiDetails('${api.id}')">
                            <i class="fas fa-info-circle mr-1"></i>Details
                        </button>
                        <button class="px-2 py-0.5 text-white text-xs rounded font-semibold shadow-lg transition-all duration-200 hover:shadow-xl hover:scale-105" 
                                style="background: linear-gradient(135deg, #14b8a6 0%, #0d9488 100%); box-shadow: 0 4px 12px rgba(20, 184, 166, 0.4);"
                                onclick="showTreeStructure('${api.id}')">
                            <i class="fas fa-sitemap mr-1"></i>Tree
                        </button>
                        <button class="px-2 py-0.5 text-white text-xs rounded font-semibold shadow-lg transition-all duration-200 hover:shadow-xl hover:scale-105" 
                                style="background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%); box-shadow: 0 4px 12px rgba(245, 158, 11, 0.4);"
                                onclick="showPerformanceAnalysis('${api.id}')">
                            <i class="fas fa-chart-line mr-1"></i>Analysis
                        </button>
                    </div>
                </td>
            </tr>
        `).join('');
        
        $('#api-list').html(html || '<tr><td colspan="7" class="px-6 py-4 text-center">No data available</td></tr>');
    }

    async function loadHistoryData() {
        try {
            const search = $('#endpoint-search').val();
            
            if (!search || search.trim() === '') {
                loadDashboardData();
                return;
            }
            
            const response = await $.get(`/perfwatch/api/stats/?search=${encodeURIComponent(search)}`);
            updateHistoryList(response.heaviest_apis || []);
        } catch (error) {
            console.error('Error loading history data:', error);
            if (error.status === 401) {
                window.location.href = '/perfwatch/dashboard/';
            }
        }
    }

    function updateHistoryList(history) {
        const html = history.map(entry => `
            <div class="border-b border-gray-700 p-4">
                <div class="flex justify-between items-start">
                    <div>
                        <div class="font-mono">${entry.endpoint || 'Unknown'}</div>
                        <div class="text-sm text-gray-400 mt-1">
                            ${entry.method || 'GET'} • ${entry.last_called ? formatTimestamp(entry.last_called) : 'Unknown time'}
                        </div>
                    </div>
                    <div class="flex items-center space-x-4">
                        ${getSeverityBadge(entry.severity)}
                        <button class="px-2 py-0.5 text-white text-xs rounded font-semibold shadow-lg transition-all duration-200 hover:shadow-xl hover:scale-105"
                                style="background: linear-gradient(135deg, #a855f7 0%, #9333ea 100%); box-shadow: 0 4px 12px rgba(168, 85, 247, 0.4);"
                                onclick="showMemoryMetrics('${entry.id}')">
                            <i class="fas fa-memory mr-1"></i>Memory
                        </button>
                        <button class="px-2 py-0.5 text-white text-xs rounded font-semibold shadow-lg transition-all duration-200 hover:shadow-xl hover:scale-105"
                                style="background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%); box-shadow: 0 4px 12px rgba(59, 130, 246, 0.4);"
                                onclick="showApiDetails('${entry.id}')">
                            <i class="fas fa-info-circle mr-1"></i>Details
                        </button>
                        <button class="px-2 py-0.5 text-white text-xs rounded font-semibold shadow-lg transition-all duration-200 hover:shadow-xl hover:scale-105"
                                style="background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%); box-shadow: 0 4px 12px rgba(245, 158, 11, 0.4);"
                                onclick="showPerformanceAnalysis('${entry.id}')">
                            <i class="fas fa-chart-line mr-1"></i>Analysis
                        </button>
                    </div>
                </div>
                <div class="grid grid-cols-3 gap-4 mt-3 text-sm">
                    <div>
                        <span class="text-gray-400">Response Time:</span>
                        <span class="ml-2">${formatDuration(entry.total_time || 0)}</span>
                    </div>
                    <div>
                        <span class="text-gray-400">DB Queries:</span>
                        <span class="ml-2">${entry.query_count || 0}</span>
                    </div>
                    <div>
                        <span class="text-gray-400">Status:</span>
                        <span class="ml-2">${entry.status_code || 200}</span>
                    </div>
                </div>
            </div>
        `).join('');

        $('#history-list').html(html || '<div class="text-center py-4">No history data available</div>');
    }

    window.showApiDetails = async function(id) {
        try {
            // First close tree drawer if it's open
            if (!$('#tree-drawer').hasClass('hidden')) {
                closeTreeDrawer();
                // Wait for tree drawer to close before opening API details
                await new Promise(resolve => setTimeout(resolve, 350));
            }
            
            // STEP 1: Open drawer immediately with loading skeletons
            $('#api-subtitle').html('<div class="h-4 bg-gray-700 rounded w-48 animate-pulse"></div>');
            $('#api-endpoint').html('<div class="h-3 bg-gray-700 rounded w-64 animate-pulse"></div>');
            $('#api-method').html('<div class="h-6 bg-gray-700 rounded w-16 animate-pulse"></div>');
            $('#api-total-time').html('<div class="h-6 bg-gray-700 rounded w-20 animate-pulse"></div>');
            $('#api-query-count').html('<div class="h-6 bg-gray-700 rounded w-12 animate-pulse"></div>');
            $('#timeline-container').html('<div class="space-y-2"><div class="h-8 bg-gray-700 rounded animate-pulse"></div><div class="h-8 bg-gray-700 rounded animate-pulse"></div><div class="h-8 bg-gray-700 rounded animate-pulse"></div></div>');
            $('#function-details').html('<div class="space-y-2"><div class="h-20 bg-gray-700 rounded animate-pulse"></div><div class="h-20 bg-gray-700 rounded animate-pulse"></div></div>');
            $('#request-headers').html('<div class="h-16 bg-gray-700 rounded animate-pulse"></div>');
            $('#request-body').html('<div class="h-16 bg-gray-700 rounded animate-pulse"></div>');
            $('#response-status').html('<div class="h-6 bg-gray-700 rounded w-16 animate-pulse"></div>');
            $('#response-headers').html('<div class="h-16 bg-gray-700 rounded animate-pulse"></div>');
            $('#response-body').html('<div class="h-16 bg-gray-700 rounded animate-pulse"></div>');
            
            // Show drawer immediately
            $('#api-details-modal').removeClass('hidden');
            setTimeout(() => {
                $('#api-details-drawer-content').removeClass('translate-x-full');
            }, 10);
            
            // STEP 2: Fetch data in background
            const data = await $.get(`/perfwatch/api/details/${id}`);
            
            // STEP 3: Update basic info first (fast)
            $('#api-subtitle').text(`${data.method} ${data.endpoint}`);
            $('#api-endpoint').text(data.endpoint);
            $('#api-method').text(data.method);
            $('#api-total-time').text(formatDuration(data.total_time));
            
            // Count total queries
            const allFunctions = data.execution_tree 
                ? flattenExecutionTree(data.execution_tree)
                : (Array.isArray(data.functions) ? data.functions : []);
            
            const totalQueries = allFunctions.reduce((sum, func) => {
                return sum + (func.queries?.length || 0);
            }, 0);
            $('#api-query-count').text(totalQueries);
            
            // STEP 4: Update timeline (medium speed) - small delay for progressive feel
            await new Promise(resolve => setTimeout(resolve, 50));
            updateTimeline(data);
            
            // STEP 5: Update function tree/details (can be heavy) - small delay
            await new Promise(resolve => setTimeout(resolve, 50));
            if (data.execution_tree) {
                updateFunctionTreeView(data.execution_tree);
            } else {
                updateFunctionDetails(data.functions);
            }
            
            // STEP 6: Update request/response data (last) - small delay
            await new Promise(resolve => setTimeout(resolve, 50));
            $('#request-headers').text(JSON.stringify(data.request.headers, null, 2));
            $('#request-body').text(JSON.stringify(data.request.body, null, 2));
            $('#response-status').html(getStatusBadge(data.status || data.response.status_code));
            $('#response-headers').text(JSON.stringify(data.response.headers, null, 2));
            $('#response-body').text(JSON.stringify(data.response.body, null, 2));
            
        } catch (error) {
            console.error('Error loading API details:', error);
            // Show error in drawer instead of leaving skeletons
            $('#function-details').html('<div class="text-center py-4 text-red-400">Error loading API details</div>');
        }
    }
    
    // Helper function to flatten execution tree into array
    function flattenExecutionTree(node, result = []) {
        if (!node) return result;
        result.push(node);
        if (Array.isArray(node.children)) {
            node.children.forEach(child => flattenExecutionTree(child, result));
        }
        return result;
    }

    function updateTimeline(data) {
        // Use execution tree directly instead of flattening
        const treeData = data.execution_tree;
        
        if (!treeData) {
            $('#timeline').html('<div class="text-center py-4 text-gray-400">No timeline data available</div>');
            return;
        }

        // Filter out Request wrapper and HTTP method functions
        function shouldShowNode(node) {
            const name = node.name || node.func_name || '';
            return !name.startsWith('Request:') && 
                   !['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'HEAD', 'OPTIONS'].includes(name);
        }

        // Find the slowest function in tree
        let slowestFunction = null;
        let maxDuration = 0;
        
        function findSlowest(node) {
            if (node.duration > maxDuration) {
                maxDuration = node.duration;
                slowestFunction = node;
            }
            if (node.children) {
                node.children.forEach(child => findSlowest(child));
            }
        }
        findSlowest(treeData);

        // Color palette for Gantt chart
        const colorPalette = [
            { bg: '#a855f7', glow: 'rgba(168, 85, 247, 0.4)', text: '#e9d5ff', icon: '🟣' },  // purple
            { bg: '#ec4899', glow: 'rgba(236, 72, 153, 0.4)', text: '#fce7f3', icon: '🔴' },  // pink
            { bg: '#06b6d4', glow: 'rgba(6, 182, 212, 0.4)', text: '#cffafe', icon: '🔵' },   // cyan
            { bg: '#14b8a6', glow: 'rgba(20, 184, 166, 0.4)', text: '#ccfbf1', icon: '🟢' },  // teal
            { bg: '#f59e0b', glow: 'rgba(245, 158, 11, 0.4)', text: '#fef3c7', icon: '🟠' },  // amber
            { bg: '#8b5cf6', glow: 'rgba(139, 92, 246, 0.4)', text: '#ddd6fe', icon: '🟣' },  // violet
            { bg: '#10b981', glow: 'rgba(16, 185, 129, 0.4)', text: '#d1fae5', icon: '🟢' },  // emerald
            { bg: '#f43f5e', glow: 'rgba(244, 63, 94, 0.4)', text: '#ffe4e6', icon: '🔴' },   // rose
        ];

        let colorIndex = 0;
        
        // Flatten tree to get all nodes with timing info
        const allNodes = [];
        let nodeCounter = 0;
        
        function flattenTree(node, level = 0, parentStart = 0, swimlane = 0) {
            if (!node) return;
            
            // Filter root level only
            if (level === 0 && !shouldShowNode(node)) {
                if (node.children && node.children.length > 0) {
                    node.children.forEach(child => flattenTree(child, 0, parentStart, swimlane));
                }
                return;
            }
            
            const nodeData = {
                id: nodeCounter++,
                name: node.name || node.func_name || 'Unknown',
                duration: node.duration,
                start: parentStart,
                end: parentStart + node.duration,
                level: level,
                swimlane: swimlane,
                queries: node.queries?.length || 0,
                memory_delta_mb: node.memory_delta_mb,
                cpu_percent: node.cpu_percent,
                objects_created: node.objects_created || 0,
                objects_destroyed: node.objects_destroyed || 0,
                gc_collected: node.gc_collected,
                error: node.error,
                isSlowest: node === slowestFunction,
                color: colorPalette[colorIndex % colorPalette.length]
            };
            
            colorIndex++;
            
            // Special colors
            if (node.error) {
                nodeData.color = { bg: '#ef4444', glow: 'rgba(239, 68, 68, 0.5)', text: '#fca5a5', icon: '⚠️' };
            } else if (nodeData.isSlowest) {
                nodeData.color = { bg: '#ea580c', glow: 'rgba(234, 88, 12, 0.6)', text: '#fed7aa', icon: '🔥' };
            } else if (nodeData.queries > 0) {
                nodeData.color = { bg: '#3b82f6', glow: 'rgba(59, 130, 246, 0.4)', text: '#bfdbfe', icon: '💾' };
            }
            
            allNodes.push(nodeData);
            
            // Process children - they start where parent starts (parallel execution)
            if (node.children && node.children.length > 0) {
                node.children.forEach((child, idx) => {
                    flattenTree(child, level + 1, parentStart, swimlane + idx);
                });
            }
        }
        
        flattenTree(treeData);
        
        if (allNodes.length === 0) {
            $('#timeline').html('<div class="text-center py-4 text-gray-400">No functions to display</div>');
            return;
        }
        
        // Calculate timeline dimensions
        const totalTime = data.total_time;
        const maxLevel = Math.max(...allNodes.map(n => n.level));
        
        // Build Gantt-style timeline
        let ganttHTML = `
            <div class="bg-gray-900 rounded-lg p-4">
                <!-- Header with controls -->
                <div class="flex items-center justify-between mb-4 pb-3 border-b border-gray-700">
                    <div>
                        <h3 class="text-lg font-bold text-white flex items-center gap-2">
                            ⏱️ Execution Timeline
                            <span class="text-sm font-normal text-gray-400">(Gantt Chart View)</span>
                        </h3>
                        <p class="text-xs text-gray-400 mt-1">Total Duration: ${formatDuration(totalTime)} • ${allNodes.length} functions</p>
                    </div>
                    <div class="flex gap-2">
                        <button onclick="zoomTimeline(0.8)" class="px-3 py-1 bg-gray-700 hover:bg-gray-600 rounded text-xs text-white transition">
                            <i class="fas fa-search-minus"></i> Zoom Out
                        </button>
                        <button onclick="zoomTimeline(1.2)" class="px-3 py-1 bg-gray-700 hover:bg-gray-600 rounded text-xs text-white transition">
                            <i class="fas fa-search-plus"></i> Zoom In
                        </button>
                        <button onclick="resetTimelineZoom()" class="px-3 py-1 bg-gray-700 hover:bg-gray-600 rounded text-xs text-white transition">
                            <i class="fas fa-redo"></i> Reset
                        </button>
                    </div>
                </div>
                
                <!-- Time scale ruler -->
                <div class="relative h-8 mb-2 border-b border-gray-700">
        `;
        
        // Add time markers
        const numMarkers = 12;
        for (let i = 0; i <= numMarkers; i++) {
            const timePoint = (totalTime * i) / numMarkers;
            const leftPercent = (i / numMarkers) * 100;
            ganttHTML += `
                <div class="absolute top-0 h-full" style="left: ${leftPercent}%;">
                    <div class="h-2 w-px bg-gray-600"></div>
                    <div class="text-xs text-gray-400 mt-1">${formatDuration(timePoint)}</div>
                </div>
            `;
        }
        
        ganttHTML += `
                </div>
                
                <!-- Timeline canvas with swimlanes -->
                <div id="gantt-canvas" class="relative overflow-x-auto overflow-y-visible" style="height: ${Math.min(allNodes.length * 40 + 50, 600)}px;">
                    <div class="relative" style="min-width: 100%; height: 100%;">
        `;
        
        // Draw each node as a bar
        allNodes.forEach((node, idx) => {
            const startPercent = (node.start / totalTime) * 100;
            const widthPercent = (node.duration / totalTime) * 100;
            const topPos = idx * 40;
            
            ganttHTML += `
                <div class="gantt-bar-wrapper absolute transition-all duration-200" 
                     style="left: ${startPercent}%; width: ${widthPercent}%; top: ${topPos}px; height: 32px;"
                     data-node-id="${node.id}">
                    
                    <!-- Background swimlane -->
                    <div class="absolute inset-0 ${idx % 2 === 0 ? 'bg-gray-800/30' : 'bg-gray-800/50'} -left-full pointer-events-none" style="width: 200%;"></div>
                    
                    <!-- Function bar -->
                    <div class="gantt-bar relative h-full cursor-pointer z-10" data-node-data='${JSON.stringify({
                        name: node.name,
                        duration: node.duration,
                        start: node.start,
                        end: node.end,
                        queries: node.queries,
                        memory_delta_mb: node.memory_delta_mb,
                        cpu_percent: node.cpu_percent,
                        objects_created: node.objects_created,
                        objects_destroyed: node.objects_destroyed,
                        gc_collected: node.gc_collected,
                        error: node.error,
                        icon: node.color.icon,
                        totalTime: totalTime
                    }).replace(/'/g, "&apos;")}'>
                        <div class="bar-inner absolute inset-0 rounded border-2 shadow-lg"
                             style="background: linear-gradient(135deg, ${node.color.bg} 0%, ${node.color.bg}dd 100%); 
                                    border-color: ${node.color.bg}; 
                                    box-shadow: 0 4px 12px ${node.color.glow};
                                    transition: all 0.2s ease;">
                            
                            <!-- Content -->
                            <div class="flex items-center h-full px-2 gap-1 pointer-events-none">
                                <span class="text-sm">${node.color.icon}</span>
                                <span class="text-xs font-semibold truncate" style="color: ${node.color.text};" title="${node.name}">
                                    ${node.name}
                                </span>
                                <span class="ml-auto text-xs font-bold text-white whitespace-nowrap">
                                    ${formatDuration(node.duration)}
                                </span>
                            </div>
                        </div>
                    </div>
                </div>
            `;
        });
        
        ganttHTML += `
                    </div>
                </div>
                
                <!-- Legend -->
                <div class="mt-4 pt-3 border-t border-gray-700 flex flex-wrap gap-3 text-xs">
                    <div class="flex items-center gap-1">
                        <div class="w-4 h-4 rounded" style="background: #ea580c;"></div>
                        <span class="text-gray-400">🔥 Slowest Function</span>
                    </div>
                    <div class="flex items-center gap-1">
                        <div class="w-4 h-4 rounded" style="background: #3b82f6;"></div>
                        <span class="text-gray-400">💾 Has DB Queries</span>
                    </div>
                    <div class="flex items-center gap-1">
                        <div class="w-4 h-4 rounded" style="background: #ef4444;"></div>
                        <span class="text-gray-400">⚠️ Has Error</span>
                    </div>
                    <div class="flex items-center gap-1 ml-auto">
                        <span class="text-gray-500">💡 Hover over bars for detailed metrics</span>
                    </div>
                </div>
            </div>
        `;
        
        $('#timeline').html(ganttHTML);
        
        // Create tooltip element in body (not inside overflow container)
        if ($('#gantt-tooltip-global').length === 0) {
            $('body').append('<div id="gantt-tooltip-global" class="fixed rounded-xl shadow-2xl p-4 w-80" style="z-index: 99999; opacity: 0; visibility: hidden; pointer-events: none; background: #1e3a5f; border: 2px solid #60a5fa; box-shadow: 0 0 30px rgba(96, 165, 250, 0.3); transition: opacity 0.2s ease, visibility 0.2s ease;"></div>');
        }
        
        const $tooltip = $('#gantt-tooltip-global');
        
        // Add hover event listeners with dynamic tooltip
        setTimeout(() => {
            const bars = $('.gantt-bar');
            console.log('🎯 Gantt bars found:', bars.length);
            
            bars.each(function(index) {
                const $bar = $(this);
                const $wrapper = $bar.closest('.gantt-bar-wrapper');
                const nodeData = JSON.parse($bar.attr('data-node-data'));
                
                $bar.on('mouseenter', function(e) {
                    console.log('🖱️ Mouse entered bar', index);
                    $wrapper.css('z-index', '999');
                    
                    // Build tooltip content
                    let tooltipHTML = `
                        <div class="font-mono font-bold mb-3 pb-2 flex items-center gap-2" style="color: #ffffff; border-bottom: 1px solid #60a5fa;">
                            ${nodeData.icon} ${nodeData.name}
                        </div>
                        <div class="grid grid-cols-2 gap-3 text-xs">
                            <div style="color: #e0e7ff;">⏱️ Duration:</div>
                            <div class="font-bold" style="color: #fde047;">${formatDuration(nodeData.duration)}</div>
                            
                            <div style="color: #e0e7ff;">📊 % of Total:</div>
                            <div class="font-semibold" style="color: #86efac;">${((nodeData.duration / nodeData.totalTime) * 100).toFixed(1)}%</div>
                            
                            <div style="color: #e0e7ff;">🕐 Start:</div>
                            <div style="color: #93c5fd;">${formatDuration(nodeData.start)}</div>
                            
                            <div style="color: #e0e7ff;">🕑 End:</div>
                            <div style="color: #93c5fd;">${formatDuration(nodeData.end)}</div>
                    `;
                    
                    if (nodeData.queries > 0) {
                        tooltipHTML += `
                            <div style="color: #e0e7ff;">💾 DB Queries:</div>
                            <div class="font-bold" style="color: #60a5fa;">${nodeData.queries}</div>
                        `;
                    }
                    
                    if (nodeData.memory_delta_mb !== undefined) {
                        tooltipHTML += `
                            <div style="color: #e0e7ff;">🧠 Memory Δ:</div>
                            <div class="font-bold" style="color: ${nodeData.memory_delta_mb > 0 ? '#f87171' : '#86efac'};">
                                ${nodeData.memory_delta_mb > 0 ? '+' : ''}${nodeData.memory_delta_mb.toFixed(2)} MB
                            </div>
                        `;
                    }
                    
                    if (nodeData.cpu_percent !== undefined && nodeData.cpu_percent > 0) {
                        tooltipHTML += `
                            <div style="color: #e0e7ff;">⚡ CPU:</div>
                            <div class="font-bold" style="color: #fb923c;">${nodeData.cpu_percent.toFixed(1)}%</div>
                        `;
                    }
                    
                    if (nodeData.objects_created > 0 || nodeData.objects_destroyed > 0) {
                        tooltipHTML += `
                            <div style="color: #e0e7ff;">🔢 Objects:</div>
                            <div class="font-semibold" style="color: #67e8f9;">+${nodeData.objects_created} -${nodeData.objects_destroyed}</div>
                        `;
                    }
                    
                    if (nodeData.gc_collected && (nodeData.gc_collected.gen0 > 0 || nodeData.gc_collected.gen1 > 0 || nodeData.gc_collected.gen2 > 0)) {
                        tooltipHTML += `
                            <div style="color: #e0e7ff;">♻️ GC:</div>
                            <div class="font-semibold" style="color: #f472b6;">
                                G0:${nodeData.gc_collected.gen0} G1:${nodeData.gc_collected.gen1} G2:${nodeData.gc_collected.gen2}
                            </div>
                        `;
                    }
                    
                    if (nodeData.error) {
                        tooltipHTML += `
                            <div class="col-span-2 mt-2 p-2 rounded" style="background: rgba(220, 38, 38, 0.2); border: 1px solid #dc2626; color: #fca5a5;">
                                ⚠️ ${nodeData.error}
                            </div>
                        `;
                    }
                    
                    tooltipHTML += '</div>';
                    $tooltip.html(tooltipHTML);
                    
                    // Position tooltip above bar
                    const barRect = $bar[0].getBoundingClientRect();
                    const tooltipWidth = 320; // w-80 = 320px
                    const left = barRect.left + (barRect.width / 2) - (tooltipWidth / 2);
                    const top = barRect.top - 10; // Above bar with 10px gap
                    
                    $tooltip.css({
                        'left': Math.max(10, Math.min(left, window.innerWidth - tooltipWidth - 10)) + 'px',
                        'top': (top - $tooltip.outerHeight()) + 'px',
                        'opacity': '1',
                        'visibility': 'visible'
                    });
                });
                
                $bar.on('mouseleave', function() {
                    console.log('🖱️ Mouse left bar', index);
                    $wrapper.css('z-index', '10');
                    $tooltip.css({
                        'opacity': '0',
                        'visibility': 'hidden'
                    });
                });
            });
            
            console.log('✅ Hover events attached');
        }, 100);
    }
    
    // Timeline zoom controls
    let timelineZoom = 1;
    window.zoomTimeline = function(factor) {
        timelineZoom *= factor;
        timelineZoom = Math.max(0.5, Math.min(timelineZoom, 5)); // Limit between 0.5x and 5x
        $('#gantt-canvas > div').css('min-width', (timelineZoom * 100) + '%');
    };
    
    window.resetTimelineZoom = function() {
        timelineZoom = 1;
        $('#gantt-canvas > div').css('min-width', '100%');
    };

    function updateFunctionDetails(functions) {

        // Add time scale markers at bottom
        const scaleMarkers = [];
        const numMarkers = 10;
        for (let i = 0; i <= numMarkers; i++) {
            const timeAtMarker = timelineStart + (timelineDuration * (i / numMarkers));
            const leftPercent = (i / numMarkers) * 100;
            scaleMarkers.push(`
                <div class="absolute top-0 h-full border-l border-gray-700 border-dashed opacity-30" style="left: calc(${leftPercent}% + 12rem)">
                    <div class="absolute -bottom-6 text-xs text-gray-500 -translate-x-1/2">
                        ${formatDuration(timeAtMarker)}
                    </div>
                </div>
            `);
        }

        const finalHtml = `
            <div class="relative">
                <!-- Time scale markers -->
                <div class="absolute inset-0 pointer-events-none">
                    ${scaleMarkers.join('')}
                </div>
                
                <!-- Timeline bars -->
                <div class="relative pb-8">
                    ${timelineHtml}
                </div>
            </div>
        `;

        $('#timeline').html(finalHtml);
    }

    function updateFunctionDetails(functions) {
        // Handle empty or invalid input
        if (!Array.isArray(functions) || functions.length === 0) {
            $('#function-details').html('<div class="text-center py-4 text-gray-400">No function details available</div>');
            return;
        }

        // Sort by duration (slowest first)
        const sortedFunctions = [...functions].sort((a, b) => b.duration - a.duration);
        
        // Generate simple list (no tree structure)
        const html = sortedFunctions.map((func, index) => {
            const queryCount = func.queries?.length || 0;
            const hasError = !!func.error;
            
            // Determine color based on performance
            let badgeColor = 'bg-green-900 text-green-300';
            const durationPercent = (func.duration / functions.reduce((sum, f) => sum + f.duration, 0)) * 100;
            
            if (hasError) {
                badgeColor = 'bg-red-900 text-red-300';
            } else if (durationPercent > 40) {
                badgeColor = 'bg-orange-900 text-orange-300';
            } else if (queryCount > 0) {
                badgeColor = 'bg-blue-900 text-blue-300';
            }
            
            return `
                <div class="border border-gray-600 rounded-lg p-3 hover:border-gray-500 transition-colors ${hasError ? 'bg-red-900/10' : ''}">
                    <div class="flex justify-between items-center">
                        <div class="flex items-center space-x-3 flex-1">
                            <div class="text-2xl font-bold text-gray-600">${index + 1}</div>
                            <div class="flex-1">
                                <div class="font-mono text-sm font-semibold text-white">${func.name || 'Unknown'}</div>
                                ${func.source ? `<div class="text-xs text-gray-400 mt-1">${func.source}</div>` : ''}
                            </div>
                        </div>
                        <div class="flex items-center space-x-4">
                            ${queryCount > 0 ? `
                                <div class="text-center">
                                    <div class="text-xs text-gray-400">Queries</div>
                                    <div class="text-sm font-bold text-blue-400">${queryCount}</div>
                                </div>
                            ` : ''}
                            <div class="text-center">
                                <div class="text-xs text-gray-400">Duration</div>
                                <div class="text-sm font-bold text-yellow-400">${formatDuration(func.duration)}</div>
                            </div>
                            <div class="px-3 py-1 rounded text-xs font-semibold ${badgeColor}">
                                ${hasError ? 'ERROR' : durationPercent > 40 ? 'SLOW' : queryCount > 0 ? 'DB' : 'OK'}
                            </div>
                        </div>
                    </div>
                    
                    ${func.error ? `
                        <div class="mt-3 bg-red-900/30 border border-red-700 rounded p-3">
                            <div class="text-xs font-bold text-red-300 mb-1">Error Details</div>
                            <pre class="text-xs text-red-200 overflow-auto whitespace-pre-wrap">${func.error}</pre>
                        </div>
                    ` : ''}
                </div>
            `;
        }).join('');
        
        $('#function-details').html(html || '<div class="text-center py-4 text-gray-400">No function details available</div>');
    }
    
    function updateSlowReasonsView(reasons) {
        // Display detailed analysis of why the API is slow
        const getSeverityIcon = (severity) => {
            return severity === 'critical' 
                ? '<i class="fas fa-exclamation-circle text-red-500"></i>'
                : '<i class="fas fa-exclamation-triangle text-yellow-500"></i>';
        };
        
        const getSeverityColor = (severity) => {
            return severity === 'critical' 
                ? 'bg-red-900/30 border-red-700'
                : 'bg-yellow-900/30 border-yellow-700';
        };
        
        const getTypeLabel = (type) => {
            const labels = {
                'slow_function': '🐌 Slow Function',
                'slow_query': '🗄️ Slow Query',
                'too_many_queries': '📊 Too Many Queries',
                'n_plus_one_query': '🔁 N+1 Query Pattern',
                'high_memory_usage': '💾 High Memory Usage',
                'overall_query_count': '⚠️ High Query Count',
                'overall_slow': '🔴 Overall Slow'
            };
            return labels[type] || type;
        };
        
        const html = reasons.map((reason, index) => `
            <div class="border ${getSeverityColor(reason.severity)} rounded-lg p-4 mb-3">
                <div class="flex items-start space-x-3">
                    <div class="text-2xl">${getSeverityIcon(reason.severity)}</div>
                    <div class="flex-1">
                        <!-- Header with type and impact -->
                        <div class="flex items-center justify-between mb-2">
                            <div class="font-semibold text-white text-base">${getTypeLabel(reason.type)}</div>
                            ${reason.impact_percent ? `
                                <div class="px-3 py-1 bg-gradient-to-r from-purple-900 to-pink-900 rounded-lg text-xs font-bold text-white">
                                    ${reason.impact_percent}% of total time
                                </div>
                            ` : ''}
                        </div>
                        
                        <!-- Main message -->
                        <div class="text-sm text-gray-300 mb-3 font-medium">${reason.message}</div>
                        
                        <!-- Metrics Grid -->
                        <div class="grid grid-cols-2 gap-2 mb-3">
                            ${reason.function ? `
                                <div class="col-span-2 text-xs">
                                    <span class="text-gray-500">Function:</span> 
                                    <code class="bg-gray-800 px-2 py-1 rounded text-blue-300 ml-1">${reason.function}</code>
                                </div>
                            ` : ''}
                            
                            ${reason.duration ? `
                                <div class="text-xs">
                                    <span class="text-gray-500">Duration:</span> 
                                    <span class="text-yellow-400 font-semibold ml-1">${formatDuration(reason.duration)}</span>
                                    ${reason.threshold ? `<span class="text-gray-600 text-[10px] ml-1">(threshold: ${formatDuration(reason.threshold)})</span>` : ''}
                                </div>
                            ` : ''}
                            
                            ${reason.query_count ? `
                                <div class="text-xs">
                                    <span class="text-gray-500">Queries:</span> 
                                    <span class="text-blue-400 font-semibold ml-1">${reason.query_count}</span>
                                    ${reason.total_query_time ? `<span class="text-gray-600 text-[10px] ml-1">(${formatDuration(reason.total_query_time)})</span>` : ''}
                                </div>
                            ` : ''}
                            
                            ${reason.memory_used ? `
                                <div class="text-xs">
                                    <span class="text-gray-500">Memory:</span> 
                                    <span class="text-purple-400 font-semibold ml-1">${reason.memory_used}MB</span>
                                    ${reason.memory_peak ? `<span class="text-purple-300 text-[10px] ml-1">(peak: ${reason.memory_peak}MB)</span>` : ''}
                                </div>
                            ` : ''}
                            
                            ${reason.memory_peak && !reason.memory_used ? `
                                <div class="text-xs">
                                    <span class="text-gray-500">Peak Memory:</span> 
                                    <span class="text-purple-400 font-semibold ml-1">${reason.memory_peak}MB</span>
                                </div>
                            ` : ''}
                            
                            ${reason.cpu_time ? `
                                <div class="text-xs">
                                    <span class="text-gray-500">CPU Time:</span> 
                                    <span class="text-orange-400 font-semibold ml-1">${formatDuration(reason.cpu_time)}</span>
                                </div>
                            ` : ''}
                            
                            ${reason.rows_affected ? `
                                <div class="text-xs">
                                    <span class="text-gray-500">Rows:</span> 
                                    <span class="text-red-400 font-semibold ml-1">${reason.rows_affected.toLocaleString()}</span>
                                </div>
                            ` : ''}
                        </div>
                        
                        <!-- Query Display -->
                        ${reason.query ? `
                            <div class="mb-3">
                                <div class="text-[10px] text-gray-500 uppercase tracking-wide mb-1">SQL Query</div>
                                <div class="bg-gray-900 rounded p-2 text-xs text-gray-300 font-mono overflow-auto max-h-32 border border-gray-700">
                                    ${reason.query}
                                </div>
                            </div>
                        ` : ''}
                        
                        ${reason.example_query ? `
                            <div class="mb-3">
                                <div class="text-[10px] text-gray-500 uppercase tracking-wide mb-1">Example N+1 Query</div>
                                <div class="bg-gray-900 rounded p-2 text-xs text-gray-300 font-mono overflow-auto max-h-32 border border-gray-700">
                                    ${reason.example_query}
                                </div>
                            </div>
                        ` : ''}
                        
                        <!-- Source Location -->
                        ${reason.source_location ? `
                            <div class="mb-3 text-xs text-gray-500 bg-gray-800/50 rounded px-2 py-1 border border-gray-700">
                                <i class="fas fa-code mr-1"></i>
                                <code class="text-gray-400">${reason.source_location}</code>
                            </div>
                        ` : ''}
                        
                        <!-- Suggestions (Multiple) -->
                        ${reason.suggestions && reason.suggestions.length > 0 ? `
                            <div class="mt-3 bg-gradient-to-br from-blue-900/40 to-indigo-900/40 border border-blue-700 rounded-lg p-3">
                                <div class="flex items-center text-xs font-bold text-blue-300 mb-2">
                                    <i class="fas fa-lightbulb mr-2 text-yellow-400"></i> 
                                    Optimization Suggestions
                                </div>
                                <ul class="space-y-1.5">
                                    ${reason.suggestions.map(sugg => `
                                        <li class="text-xs text-blue-200 flex items-start">
                                            <span class="mr-2 mt-0.5">•</span>
                                            <span>${sugg}</span>
                                        </li>
                                    `).join('')}
                                </ul>
                            </div>
                        ` : ''}
                        
                        <!-- Single Suggestion (Backward Compatibility) -->
                        ${reason.suggestion && (!reason.suggestions || reason.suggestions.length === 0) ? `
                            <div class="mt-3 bg-gradient-to-br from-blue-900/40 to-indigo-900/40 border border-blue-700 rounded-lg p-3">
                                <div class="flex items-start text-xs">
                                    <i class="fas fa-lightbulb mr-2 text-yellow-400 mt-0.5"></i> 
                                    <div>
                                        <span class="font-bold text-blue-300">Suggestion:</span>
                                        <span class="text-blue-200 ml-1">${reason.suggestion}</span>
                                    </div>
                                </div>
                            </div>
                        ` : ''}
                    </div>
                </div>
            </div>
        `).join('');
        
        $('#slow-reasons-content').html(html);
    }

    function closeModal() {
        $('#api-details-drawer-content').addClass('translate-x-full');
        setTimeout(() => {
            $('#api-details-modal').addClass('hidden');
        }, 300);
    }

    function closeTreeDrawer() {
        $('#tree-drawer-content').addClass('translate-x-full');
        setTimeout(() => {
            $('#tree-drawer').addClass('hidden');
        }, 300);
    }
    
    window.closeAnalysisModal = function() {
        $('#analysis-drawer-content').addClass('translate-x-full');
        setTimeout(() => {
            $('#analysis-modal').addClass('hidden');
        }, 300);
    }
    
    window.closeMemoryDrawer = function() {
        $('#memory-drawer-content').addClass('translate-x-full');
        setTimeout(() => {
            $('#memory-modal').addClass('hidden');
        }, 300);
    }
    
    window.showMemoryMetrics = async function(id) {
        try {
            // Close other drawers if open
            if (!$('#api-details-modal').hasClass('hidden')) {
                closeModal();
                await new Promise(resolve => setTimeout(resolve, 350));
            }
            if (!$('#tree-drawer').hasClass('hidden')) {
                closeTreeDrawer();
                await new Promise(resolve => setTimeout(resolve, 350));
            }
            if (!$('#analysis-modal').hasClass('hidden')) {
                closeAnalysisModal();
                await new Promise(resolve => setTimeout(resolve, 350));
            }
            
            const response = await $.get(`/perfwatch/api/details/${id}`);
            
            // Check if we have an error response
            if (response.error) {
                throw new Error(response.error);
            }
            
            // Build memory metrics HTML
            const memoryDelta = response.memory_delta_mb || 0;
            const memoryLeakWarning = memoryDelta > 0 ? 
                '<span class="text-red-400 ml-2"><i class="fas fa-exclamation-triangle"></i> Potential Memory Leak</span>' : 
                '<span class="text-green-400 ml-2"><i class="fas fa-check-circle"></i> Memory Freed</span>';
            
            const metricsHTML = `
                <div class="bg-gray-800 rounded-lg p-6">
                    <div class="flex items-center justify-between mb-6">
                        <div>
                            <h3 class="text-xl font-bold text-white">📊 Memory Metrics</h3>
                            <p class="text-gray-400 mt-1">${response.method} ${response.endpoint}</p>
                        </div>
                        <button onclick="closeMemoryDrawer()" class="text-gray-400 hover:text-white">
                            <i class="fas fa-times text-2xl"></i>
                        </button>
                    </div>
                    
                    <!-- Memory Section -->
                    <div class="mb-6 bg-purple-900/20 border border-purple-700 rounded-lg p-4">
                        <h4 class="text-purple-400 font-semibold mb-4 flex items-center text-lg">
                            <i class="fas fa-memory mr-2"></i>💾 Memory Usage
                        </h4>
                        <div class="space-y-4">
                            <div class="bg-gray-900/50 rounded-lg p-3">
                                <div class="flex justify-between items-center mb-2">
                                    <span class="text-gray-300 text-sm">Memory Status</span>
                                    <span class="text-xs px-2 py-1 rounded ${memoryDelta > 0 ? 'bg-red-500/20 text-red-400' : 'bg-green-500/20 text-green-400'}">
                                        ${memoryDelta > 0 ? '⚠️ Increased' : '✅ Optimized'}
                                    </span>
                                </div>
                                <div class="text-3xl font-bold ${memoryDelta > 0 ? 'text-red-400' : 'text-green-400'}">
                                    ${memoryDelta > 0 ? '+' : ''}${Math.abs(memoryDelta).toFixed(2)} MB
                                </div>
                                <p class="text-xs text-gray-400 mt-1">
                                    ${memoryDelta > 0 ? 'Memory consumption increased during request' : 'Memory was freed/recycled during request'}
                                </p>
                            </div>
                            
                            <div class="grid grid-cols-2 gap-3">
                                <div class="bg-gray-900/50 rounded-lg p-3">
                                    <span class="text-gray-400 text-xs block mb-1">Before Request</span>
                                    <div class="text-xl font-semibold text-white">${(response.memory_before_mb || 0).toFixed(2)} MB</div>
                                    <p class="text-xs text-gray-500 mt-1">Initial memory</p>
                                </div>
                                <div class="bg-gray-900/50 rounded-lg p-3">
                                    <span class="text-gray-400 text-xs block mb-1">After Request</span>
                                    <div class="text-xl font-semibold text-white">${(response.memory_after_mb || 0).toFixed(2)} MB</div>
                                    <p class="text-xs text-gray-500 mt-1">Final memory</p>
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <!-- Objects & GC Section -->
                    <div class="mb-6 bg-pink-900/20 border border-pink-700 rounded-lg p-4">
                        <h4 class="text-pink-400 font-semibold mb-4 flex items-center text-lg">
                            <i class="fas fa-cubes mr-2"></i>🧹 Garbage Collection & Objects
                        </h4>
                        
                        <div class="mb-4 bg-gray-900/50 rounded-lg p-3">
                            <div class="flex justify-between items-center mb-3">
                                <span class="text-gray-300 text-sm">GC Status</span>
                                <span class="text-lg font-semibold ${response.gc_enabled ? 'text-green-400' : 'text-red-400'}">
                                    ${response.gc_enabled ? '✅ Active' : '⚠️ Disabled'}
                                </span>
                            </div>
                            <div class="grid grid-cols-3 gap-2 text-center">
                                <div class="bg-gray-800 rounded p-2">
                                    <div class="text-xs text-gray-400">Gen 0</div>
                                    <div class="text-lg font-bold text-white">${(response.gc_collected?.gen0 || 0)}</div>
                                    <div class="text-xs text-gray-500">Young objects</div>
                                </div>
                                <div class="bg-gray-800 rounded p-2">
                                    <div class="text-xs text-gray-400">Gen 1</div>
                                    <div class="text-lg font-bold text-white">${(response.gc_collected?.gen1 || 0)}</div>
                                    <div class="text-xs text-gray-500">Mid-age objects</div>
                                </div>
                                <div class="bg-gray-800 rounded p-2">
                                    <div class="text-xs text-gray-400">Gen 2</div>
                                    <div class="text-lg font-bold text-white">${(response.gc_collected?.gen2 || 0)}</div>
                                    <div class="text-xs text-gray-500">Old objects</div>
                                </div>
                            </div>
                        </div>
                        
                        <div class="bg-gray-900/50 rounded-lg p-3">
                            <div class="flex items-center justify-between mb-2">
                                <span class="text-gray-300 text-sm">Net Object Change</span>
                                ${(response.object_count_delta || 0) > 0 
                                    ? '<i class="fas fa-arrow-up text-yellow-400"></i>' 
                                    : (response.object_count_delta || 0) < 0 
                                        ? '<i class="fas fa-arrow-down text-green-400"></i>' 
                                        : '<i class="fas fa-equals text-gray-400"></i>'}
                            </div>
                            <div class="text-center">
                                <div class="text-3xl font-bold ${
                                    (response.object_count_delta || 0) > 0 ? 'text-yellow-400' : 
                                    (response.object_count_delta || 0) < 0 ? 'text-green-400' : 'text-gray-400'
                                }">
                                    ${(response.object_count_delta || 0) > 0 ? '+' : ''}${(response.object_count_delta || 0).toLocaleString()}
                                </div>
                                <p class="text-xs text-gray-400 mt-2">
                                    ${(response.object_count_delta || 0) > 0 
                                        ? `At least ${response.object_count_delta} objects created (some may have been destroyed too)` 
                                        : (response.object_count_delta || 0) < 0 
                                            ? `At least ${Math.abs(response.object_count_delta)} objects destroyed (some may have been created too)` 
                                            : 'No net change in object count'}
                                </p>
                            </div>
                            ${(response.gc_collected?.gen0 || 0) > 0 || (response.gc_collected?.gen1 || 0) > 0 || (response.gc_collected?.gen2 || 0) > 0 
                                ? `<div class="mt-3 pt-3 border-t border-gray-700 text-center">
                                    <p class="text-xs text-green-400">
                                        <i class="fas fa-broom mr-1"></i>
                                        Garbage collector ran ${(response.gc_collected?.gen0 || 0) + (response.gc_collected?.gen1 || 0) + (response.gc_collected?.gen2 || 0)} times during request
                                    </p>
                                   </div>` 
                                : ''}
                        </div>
                    </div>
                    
                    <!-- CPU Section -->
                    <div class="mb-6 bg-orange-900/20 border border-orange-700 rounded-lg p-4">
                        <h4 class="text-orange-400 font-semibold mb-4 flex items-center text-lg">
                            <i class="fas fa-microchip mr-2"></i>⚡ CPU Performance
                        </h4>
                        <div class="grid grid-cols-3 gap-3">
                            <div class="bg-gray-900/50 rounded-lg p-3">
                                <span class="text-gray-400 text-xs block mb-1">CPU Usage</span>
                                <div class="text-2xl font-bold text-orange-400">${(response.cpu_percent || 0).toFixed(1)}%</div>
                                <div class="w-full bg-gray-700 rounded-full h-2 mt-2">
                                    <div class="bg-orange-400 h-2 rounded-full" style="width: ${Math.min(response.cpu_percent || 0, 100)}%"></div>
                                </div>
                            </div>
                            <div class="bg-gray-900/50 rounded-lg p-3">
                                <span class="text-gray-400 text-xs block mb-1">User Time</span>
                                <div class="text-xl font-semibold text-white">${((response.cpu_time_user || 0) * 1000).toFixed(1)} ms</div>
                                <p class="text-xs text-gray-500 mt-1">Application code</p>
                            </div>
                            <div class="bg-gray-900/50 rounded-lg p-3">
                                <span class="text-gray-400 text-xs block mb-1">System Time</span>
                                <div class="text-xl font-semibold text-white">${((response.cpu_time_system || 0) * 1000).toFixed(1)} ms</div>
                                <p class="text-xs text-gray-500 mt-1">OS operations</p>
                            </div>
                        </div>
                    </div>
                    
                    <!-- I/O Section -->
                    <div class="bg-blue-900/20 border border-blue-700 rounded-lg p-4">
                        <h4 class="text-blue-400 font-semibold mb-4 flex items-center text-lg">
                            <i class="fas fa-exchange-alt mr-2"></i>💿 Disk I/O Operations
                        </h4>
                        <div class="grid grid-cols-2 gap-3">
                            <div class="bg-gray-900/50 rounded-lg p-3">
                                <div class="flex items-center justify-between mb-2">
                                    <span class="text-gray-400 text-xs">Data Read</span>
                                    <i class="fas fa-download text-blue-400"></i>
                                </div>
                                <div class="text-2xl font-bold text-blue-400">
                                    ${((response.io_read_bytes || 0) / 1024).toFixed(2)} KB
                                </div>
                                <p class="text-xs text-gray-500 mt-1">
                                    ${((response.io_read_bytes || 0) / (1024*1024)).toFixed(3)} MB read from disk
                                </p>
                            </div>
                            <div class="bg-gray-900/50 rounded-lg p-3">
                                <div class="flex items-center justify-between mb-2">
                                    <span class="text-gray-400 text-xs">Data Written</span>
                                    <i class="fas fa-upload text-green-400"></i>
                                </div>
                                <div class="text-2xl font-bold text-green-400">
                                    ${((response.io_write_bytes || 0) / 1024).toFixed(2)} KB
                                </div>
                                <p class="text-xs text-gray-500 mt-1">
                                    ${((response.io_write_bytes || 0) / (1024*1024)).toFixed(3)} MB written to disk
                                </p>
                            </div>
                        </div>
                    </div>
                </div>
            `;
            
            // Show in memory modal (use separate drawer from analysis)
            $('#memory-drawer-content').html(metricsHTML);
            $('#memory-modal').removeClass('hidden');
            setTimeout(() => {
                $('#memory-drawer-content').removeClass('translate-x-full');
            }, 10);
        } catch (error) {
            console.error('Error loading memory metrics:', error);
            $('#memory-drawer-content').html(`
                <div class="text-center py-8 text-red-400">
                    <i class="fas fa-exclamation-triangle text-4xl mb-3"></i>
                    <p class="text-lg">Error loading memory metrics</p>
                    <p class="text-sm mt-2">${error.message || 'Unknown error'}</p>
                </div>
            `);
        }
    }
    
    window.showPerformanceAnalysis = async function(id) {
        try {
            // Close other drawers if open
            if (!$('#api-details-modal').hasClass('hidden')) {
                closeModal();
                await new Promise(resolve => setTimeout(resolve, 350));
            }
            if (!$('#tree-drawer').hasClass('hidden')) {
                closeTreeDrawer();
                await new Promise(resolve => setTimeout(resolve, 350));
            }
            if (!$('#memory-modal').hasClass('hidden')) {
                closeMemoryDrawer();
                await new Promise(resolve => setTimeout(resolve, 350));
            }
            
            const data = await $.get(`/perfwatch/api/details/${id}`);
            
            // Update header
            $('#analysis-endpoint-info').text(`${data.method} ${data.endpoint}`);
            $('#analysis-total-time').text(formatDuration(data.total_time));
            $('#analysis-severity').html(getSeverityBadge(data.severity));
            
            // Show slow reasons
            if (data.slow_reasons && data.slow_reasons.length > 0) {
                updateSlowReasonsView(data.slow_reasons);
            } else {
                $('#slow-reasons-content').html(`
                    <div class="text-center py-8 text-gray-400">
                        <i class="fas fa-check-circle text-green-500 text-4xl mb-3"></i>
                        <p class="text-lg">No performance issues detected!</p>
                        <p class="text-sm mt-2">This API is performing within acceptable thresholds.</p>
                    </div>
                `);
            }
            
            // Show analysis modal
            $('#analysis-modal').removeClass('hidden');
            setTimeout(() => {
                $('#analysis-drawer-content').removeClass('translate-x-full');
            }, 10);
        } catch (error) {
            console.error('Error loading performance analysis:', error);
        }
    }

    window.showTreeStructure = async function(id) {
        try {
            // First close API details drawer if it's open
            if (!$('#api-details-modal').hasClass('hidden')) {
                closeModal();
                // Wait for API details drawer to close before opening tree
                await new Promise(resolve => setTimeout(resolve, 350));
            }
            
            // STEP 1: Open drawer immediately with loading skeletons
            $('#tree-endpoint-info').html('<div class="h-4 bg-gray-700 rounded w-64 animate-pulse"></div>');
            $('#tree-total-time').html('<div class="h-6 bg-gray-700 rounded w-20 animate-pulse"></div>');
            $('#tree-function-count').html('<div class="h-6 bg-gray-700 rounded w-12 animate-pulse"></div>');
            $('#tree-query-count').html('<div class="h-6 bg-gray-700 rounded w-12 animate-pulse"></div>');
            $('#tree-query-time').html('<div class="h-6 bg-gray-700 rounded w-20 animate-pulse"></div>');
            $('#tree-structure-content').html('<div class="space-y-2"><div class="h-16 bg-gray-700 rounded animate-pulse"></div><div class="h-16 bg-gray-700 rounded animate-pulse ml-4"></div><div class="h-16 bg-gray-700 rounded animate-pulse ml-8"></div><div class="h-16 bg-gray-700 rounded animate-pulse ml-4"></div></div>');
            
            // Show drawer immediately
            $('#tree-drawer').removeClass('hidden');
            setTimeout(() => {
                $('#tree-drawer-content').removeClass('translate-x-full');
            }, 10);
            
            // STEP 2: Fetch data in background
            const data = await $.get(`/perfwatch/api/details/${id}`);
            
            // STEP 3: Update header info first (fast)
            $('#tree-endpoint-info').text(`${data.method} ${data.endpoint} - ${formatDuration(data.total_time)}`);
            
            // STEP 4: Calculate and show stats (medium speed)
            await new Promise(resolve => setTimeout(resolve, 50));
            const stats = calculateTreeStats(data.execution_tree || data.functions);
            $('#tree-total-time').text(formatDuration(data.total_time));
            $('#tree-function-count').text(stats.functionCount);
            $('#tree-query-count').text(stats.queryCount);
            $('#tree-query-time').text(formatDuration(stats.totalQueryTime));
            
            // STEP 5: Build and render tree structure (can be heavy)
            await new Promise(resolve => setTimeout(resolve, 50));
            const treeData = data.execution_tree || buildTreeFromFunctions(data.functions);
            const treeHtml = buildInteractiveTree(treeData, data);
            $('#tree-structure-content').html(treeHtml);
            
            // STEP 6: Expand nodes after render - increased delay for DOM to settle
            setTimeout(() => {
                expandAllTreeNodes();
            }, 300);  // Increased from 100ms to 300ms
            
            // Setup tree node click handlers
            setupTreeNodeHandlers();
        } catch (error) {
            console.error('Error loading execution tree:', error);
            // Show error in drawer
            $('#tree-structure-content').html('<div class="text-center py-4 text-red-400">Error loading execution tree</div>');
        }
    }

    function calculateTreeStats(node, stats = { functionCount: 0, queryCount: 0, totalQueryTime: 0 }) {
        if (!node) return stats;
        
        if (Array.isArray(node)) {
            node.forEach(n => calculateTreeStats(n, stats));
            return stats;
        }
        
        stats.functionCount++;
        
        if (Array.isArray(node.queries)) {
            stats.queryCount += node.queries.length;
            node.queries.forEach(q => {
                stats.totalQueryTime += (q.duration || q.time_ms || 0);
            });
        }
        
        if (Array.isArray(node.children)) {
            node.children.forEach(child => calculateTreeStats(child, stats));
        }
        
        return stats;
    }

    function buildTreeFromFunctions(functions) {
        if (!Array.isArray(functions) || functions.length === 0) return null;
        
        // Assume first function is root
        const root = functions[0];
        root.children = functions.slice(1);
        return root;
    }

    function buildInteractiveTree(node, apiData, level = 0, path = '0') {
        if (!node) return '<div class="text-gray-400">No execution tree available</div>';
        
        const nodeId = `tree-node-${path}`;
        const hasChildren = Array.isArray(node.children) && node.children.length > 0;
        
        // Filter queries to show ONLY those belonging to this function
        const currentFuncName = node.func_name || node.name;
        let ownQueries = [];
        let orphanQueries = [];
        let childFunctionNames = [];
        
        // Get all child function names
        if (hasChildren) {
            childFunctionNames = node.children.map(child => child.func_name || child.name).filter(Boolean);
        }
        
        if (Array.isArray(node.queries) && node.queries.length > 0) {
            node.queries.forEach(query => {
                const queryFuncName = query.function_name;
                
                // Skip if query belongs to a child function (duplicate prevention)
                if (childFunctionNames.includes(queryFuncName)) {
                    return; // This query will be shown under the child
                }
                
                if (queryFuncName && queryFuncName === currentFuncName) {
                    ownQueries.push(query);
                } else {
                    // This query doesn't belong here - it's an orphan
                    orphanQueries.push(query);
                }
            });
        }
        
        const hasQueries = ownQueries.length > 0;
        const hasOrphans = orphanQueries.length > 0;
        const indent = level * 20;
        
        // Calculate query time for this node (only own queries)
        let queryTime = 0;
        if (hasQueries) {
            queryTime = ownQueries.reduce((sum, q) => sum + (q.duration || q.time_ms || 0), 0);
        }
        
        // Determine node color based on duration
        const durationPercent = apiData.total_time > 0 ? (node.duration / apiData.total_time) * 100 : 0;
        let colorClass = 'bg-gray-700';
        let borderColor = 'border-gray-600';
        let iconColor = 'text-gray-400';
        
        if (durationPercent > 50) {
            colorClass = 'bg-red-900/20';
            borderColor = 'border-red-600';
            iconColor = 'text-red-400';
        } else if (durationPercent > 25) {
            colorClass = 'bg-yellow-900/20';
            borderColor = 'border-yellow-600';
            iconColor = 'text-yellow-400';
        } else {
            colorClass = 'bg-green-900/20';
            borderColor = 'border-green-600';
            iconColor = 'text-green-400';
        }
        
        let html = `
            <div class="tree-node" style="margin-left: ${indent}px" data-node-id="${nodeId}">
                <div class="border ${borderColor} ${colorClass} rounded-lg p-3 mb-2 cursor-pointer hover:shadow-lg transition-all" 
                     onclick="toggleTreeNode('${nodeId}')">
                    <div class="flex items-center justify-between">
                        <div class="flex items-center space-x-3 flex-1">
                            ${hasChildren ? `<i class="fas fa-chevron-right ${iconColor} tree-toggle" id="toggle-${nodeId}"></i>` : `<i class="fas fa-circle ${iconColor}" style="font-size: 0.5rem;"></i>`}
                            <div class="flex-1">
                                <div class="flex items-center space-x-2">
                                    <span class="font-mono text-sm font-semibold">${node.name || 'Unknown'}</span>
                                    ${node.error ? '<i class="fas fa-exclamation-circle text-red-500" title="Error occurred"></i>' : ''}
                                </div>
                                ${node.source ? `<div class="text-xs text-gray-400 mt-1">${node.source}</div>` : ''}
                            </div>
                        </div>
                        <div class="flex items-center space-x-4 text-sm">
                            <div class="text-right">
                                <div class="font-semibold">${formatDuration(node.duration)}</div>
                                <div class="text-xs text-gray-400">${durationPercent.toFixed(1)}% of total</div>
                            </div>
                            ${node.memory_delta_mb !== undefined && Math.abs(node.memory_delta_mb) > 0.01 ? `
                                <div class="px-2 py-1 bg-purple-900 rounded text-xs" title="Memory change">
                                    <i class="fas fa-memory"></i> ${node.memory_delta_mb > 0 ? '+' : ''}${node.memory_delta_mb.toFixed(2)} MB
                                </div>
                            ` : ''}
                            ${node.cpu_percent !== undefined && node.cpu_percent > 0 ? `
                                <div class="px-2 py-1 bg-orange-900 rounded text-xs" title="CPU usage">
                                    <i class="fas fa-microchip"></i> ${node.cpu_percent.toFixed(1)}%
                                </div>
                            ` : ''}
                            ${(node.objects_created > 0 || node.objects_destroyed > 0) ? `
                                <div class="px-2 py-1 bg-cyan-900 rounded text-xs" title="Object allocations">
                                    <i class="fas fa-cube"></i> +${node.objects_created} -${node.objects_destroyed}
                                </div>
                            ` : ''}
                            ${node.gc_collected && (node.gc_collected.gen0 > 0 || node.gc_collected.gen1 > 0 || node.gc_collected.gen2 > 0) ? `
                                <div class="px-2 py-1 bg-pink-900 rounded text-xs" title="Garbage collections">
                                    <i class="fas fa-recycle"></i> G0:${node.gc_collected.gen0} G1:${node.gc_collected.gen1} G2:${node.gc_collected.gen2}
                                </div>
                            ` : ''}
                            ${hasQueries ? `
                                <div class="px-2 py-1 bg-blue-900 rounded text-xs" title="Direct queries in this function">
                                    <i class="fas fa-database"></i> ${ownQueries.length} ${ownQueries.length === 1 ? 'query' : 'queries'} (${formatDuration(queryTime)})
                                </div>
                            ` : ''}
                            ${hasChildren && !hasQueries ? `
                                <div class="px-2 py-1 bg-gray-700 rounded text-xs text-gray-400" title="No direct queries, but child functions may have queries">
                                    <i class="fas fa-database"></i> 0 queries
                                </div>
                            ` : ''}
                            ${hasOrphans ? `
                                <div class="px-2 py-1 bg-yellow-900 rounded text-xs" title="These queries should belong to child functions">
                                    <i class="fas fa-exclamation-triangle"></i> ${orphanQueries.length} orphaned
                                </div>
                            ` : ''}
                        </div>
                    </div>
                    
                    ${node.error ? `
                        <div class="mt-2 p-2 bg-red-900/30 rounded text-xs text-red-300">
                            <i class="fas fa-exclamation-triangle mr-1"></i> ${node.error}
                        </div>
                    ` : ''}
                </div>
                
                <!-- Queries Section (Display First - Right After Function) -->
                ${hasQueries ? `
                    <div class="tree-queries hidden ml-8 mb-2" id="queries-${nodeId}">
                        ${ownQueries.map((query, idx) => `
                            <div class="border border-blue-600 bg-blue-900/10 rounded p-3 mb-2">
                                <div class="flex justify-between items-center mb-2">
                                    <div class="flex items-center space-x-2">
                                        <div class="text-xs font-semibold text-blue-400">
                                            <i class="fas fa-database mr-1"></i> Query #${idx + 1}
                                        </div>
                                        ${query.function_name ? `
                                            <span class="text-xs px-2 py-0.5 bg-blue-800 rounded text-blue-200">
                                                ${query.function_name}
                                            </span>
                                        ` : ''}
                                    </div>
                                    <div class="text-sm text-gray-300">${formatDuration(query.duration || query.time_ms || 0)}</div>
                                </div>
                                <pre class="text-xs bg-gray-900 p-2 rounded overflow-auto max-h-40 text-gray-300">${query.sql || query.query || 'No query text'}</pre>
                                ${query.params ? `
                                    <div class="mt-2 text-xs text-gray-400">
                                        <span class="font-semibold">Params:</span> ${JSON.stringify(query.params)}
                                    </div>
                                ` : ''}
                                ${query.rows_affected ? `
                                    <div class="mt-1 text-xs text-gray-400">
                                        <span class="font-semibold">Rows:</span> ${query.rows_affected}
                                    </div>
                                ` : ''}
                            </div>
                        `).join('')}
                    </div>
                ` : ''}
                
                <!-- Orphan Queries Section (Queries that don't belong to this function) -->
                ${hasOrphans ? `
                    <div class="tree-queries hidden ml-8 mb-2" id="queries-${nodeId}">
                        <div class="text-xs text-orange-400 mb-2 p-2 bg-orange-900/20 border border-orange-700 rounded">
                            <i class="fas fa-exclamation-triangle mr-1"></i> 
                            Warning: These queries have function_name='${orphanQueries[0].function_name}' but are stored under '${currentFuncName}'
                        </div>
                        ${orphanQueries.map((query, idx) => `
                            <div class="border border-orange-600 bg-orange-900/10 rounded p-3 mb-2">
                                <div class="flex justify-between items-center mb-2">
                                    <div class="flex items-center space-x-2">
                                        <div class="text-xs font-semibold text-orange-400">
                                            <i class="fas fa-database mr-1"></i> Misplaced Query #${idx + 1}
                                        </div>
                                        ${query.function_name ? `
                                            <span class="text-xs px-2 py-0.5 bg-orange-800 rounded text-orange-200">
                                                Should be in: ${query.function_name}
                                            </span>
                                        ` : ''}
                                    </div>
                                    <div class="text-sm text-gray-300">${formatDuration(query.duration || query.time_ms || 0)}</div>
                                </div>
                                <pre class="text-xs bg-gray-900 p-2 rounded overflow-auto max-h-40 text-gray-300">${query.sql || query.query || 'No query text'}</pre>
                                ${query.params ? `
                                    <div class="mt-2 text-xs text-gray-400">
                                        <span class="font-semibold">Params:</span> ${JSON.stringify(query.params)}
                                    </div>
                                ` : ''}
                            </div>
                        `).join('')}
                    </div>
                ` : ''}
                
                <!-- Children Section (Display After Queries) -->
                ${hasChildren ? `
                    <div class="tree-children hidden" id="children-${nodeId}">
                        ${node.children.map((child, idx) => buildInteractiveTree(child, apiData, level + 1, `${path}-${idx}`)).join('')}
                    </div>
                ` : ''}
            </div>
        `;
        
        return html;
    }

    function setupTreeNodeHandlers() {
        // Remove old handlers
        $(document).off('click', '.tree-node');
    }

    window.toggleTreeNode = function(nodeId) {
        const toggleIcon = $(`#toggle-${nodeId}`);
        const queriesSection = $(`#queries-${nodeId}`);
        const childrenSection = $(`#children-${nodeId}`);
        
        // Toggle icon
        if (toggleIcon.length) {
            toggleIcon.toggleClass('fa-chevron-right fa-chevron-down');
        }
        
        // Toggle queries and children
        queriesSection.toggleClass('hidden');
        childrenSection.toggleClass('hidden');
    }
    
    window.toggleMetricsPanel = function(nodeId) {
        const panel = $(`#metrics-panel-${nodeId}`);
        const toggleIcon = $(`#metrics-toggle-${nodeId}`);
        
        panel.toggleClass('hidden');
        toggleIcon.toggleClass('fa-chevron-down fa-chevron-up');
    }

    function expandAllTreeNodes() {
        // Find all toggle icons and expand them
        $('.tree-toggle').each(function() {
            const toggleIcon = $(this);
            const nodeId = toggleIcon.attr('id').replace('toggle-', '');
            
            // Change icon to expanded state
            if (toggleIcon.hasClass('fa-chevron-right')) {
                toggleIcon.removeClass('fa-chevron-right').addClass('fa-chevron-down');
            }
            
            // Show queries and children
            $(`#queries-${nodeId}`).removeClass('hidden');
            $(`#children-${nodeId}`).removeClass('hidden');
        });
    }

    function closeModal() {
        $('#api-details-modal').addClass('hidden');
    }

    function updateFunctionTreeView(executionTree) {
        if (!executionTree) {
            $('#function-details').html('<div class="text-center py-4 text-gray-400">No function details available</div>');
            return;
        }

        function generateTreeNode(node, level = 0) {
            let html = `
                <div class="border border-gray-600 rounded-lg p-4 mb-2" style="margin-left: ${level * 16}px">
                    <div class="flex justify-between items-center mb-2">
                        <div class="flex items-center">
                            <div class="font-mono text-sm">${node.name || 'Unknown'}</div>
                            ${node.source ? `<span class="text-xs text-gray-400 ml-2">${node.source}</span>` : ''}
                        </div>
                        <div class="text-sm">
                            <span class="text-gray-400">${formatDuration(node.duration)}</span>
                            ${node.start_time ? `<span class="text-xs text-gray-500 ml-2">(at ${formatTimestamp(node.start_time)})</span>` : ''}
                        </div>
                    </div>
                    ${Array.isArray(node.queries) && node.queries.length > 0 ? node.queries.map(query => `
                        <div class="bg-gray-900 p-3 rounded mt-2">
                            <div class="flex justify-between items-center mb-1">
                                <div class="text-blue-400 text-sm flex items-center">
                                    <span class="mr-2">Query</span>
                                    ${query.db_type ? `<span class="text-xs px-2 py-1 bg-blue-900 rounded">${query.db_type}</span>` : ''}
                                </div>
                                <div class="text-sm text-gray-400">${formatDuration(query.duration)}</div>
                            </div>
                            <pre class="text-xs overflow-auto whitespace-pre-wrap break-words">${query.sql || 'No query text available'}</pre>
                            ${query.rows_affected ? `<div class="text-xs text-gray-400 mt-1">Rows affected: ${query.rows_affected}</div>` : ''}
                        </div>
                    `).join('') : ''}
                    ${node.error ? `
                        <div class="bg-red-900/20 text-red-400 p-3 rounded mt-2">
                            <div class="font-bold mb-1">Error</div>
                            <pre class="text-xs overflow-auto whitespace-pre-wrap break-words">${node.error}</pre>
                        </div>
                    ` : ''}
                </div>
            `;

            // Recursively add children
            if (Array.isArray(node.children) && node.children.length > 0) {
                html += node.children.map(child => generateTreeNode(child, level + 1)).join('');
            }

            return html;
        }

        const html = generateTreeNode(executionTree);
        $('#function-details').html(html);
    }

    // Utility functions
    function formatDuration(ms) {
        // Handle null/undefined/0
        if (ms === null || ms === undefined || ms === 0) {
            return '0ms';
        }
        
        // Handle numbers
        if (typeof ms === 'number') {
            // Treat all numbers as milliseconds
            if (ms < 1) {
                return `${ms.toFixed(2)}ms`;
            } else if (ms < 1000) {
                return `${ms.toFixed(2)}ms`;
            } else {
                return `${(ms / 1000).toFixed(2)}s`;
            }
        }
        return 'N/A';
    }

    function formatTimestamp(timestamp) {
        // Return 'N/A' for null or undefined
        if (!timestamp) return 'N/A';

        // Handle ISO 8601 timestamp strings from Python's isoformat()
        try {
            const date = new Date(timestamp);
            if (isNaN(date.getTime())) {
                // If direct parsing fails, try wrapping in quotes if it's not already
                if (!timestamp.startsWith('"') && !timestamp.endsWith('"')) {
                    const quoted = new Date(JSON.parse(`"${timestamp}"`));
                    if (!isNaN(quoted.getTime())) {
                        return quoted.toLocaleString();
                    }
                }
                console.warn('Invalid timestamp:', timestamp);
                return 'N/A';
            }
            return date.toLocaleString();
        } catch (e) {
            console.error('Error formatting timestamp:', e);
            return 'N/A';
        }
    }

    function getSeverityBadge(severity) {
        const colors = {
            critical: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-300',
            warning: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-300',
            normal: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300'
        };
        return `<span class="px-2.5 py-0.5 text-xs font-medium rounded-full ${colors[severity] || ''}">${severity}</span>`;
    }

    function getStatusBadge(status) {
        const colors = {
            success: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300',
            error: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-300',
            warning: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-300'
        };
        const type = status < 300 ? 'success' : status < 400 ? 'warning' : 'error';
        return `<span class="px-2.5 py-0.5 text-xs font-medium rounded-full ${colors[type]}">${status}</span>`;
    }

    function debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }
});
// Profiling toggle functions
async function loadProfilingStatus() {
    try {
        const response = await $.get('/perfwatch/api/profiling-status');
        updateProfilingUI(response.profiling_enabled);
    } catch (error) {
        console.error('Error loading profiling status:', error);
    }
}

async function toggleProfiling() {
    try {
        const response = await $.post('/perfwatch/api/toggle-profiling');
        updateProfilingUI(response.profiling_enabled);
        
        // Show toast notification
        const message = response.message || (response.profiling_enabled ? 'Profiling enabled' : 'Profiling disabled');
        showToast(message, response.profiling_enabled ? 'success' : 'info');
    } catch (error) {
        console.error('Error toggling profiling:', error);
        showToast('Failed to toggle profiling', 'error');
    }
}

function updateProfilingUI(enabled) {
    const button = $('#profiling-toggle');
    const icon = $('#profiling-status-icon');
    const text = $('#profiling-status-text');
    
    if (enabled) {
        button.removeClass('bg-red-900 hover:bg-red-800').addClass('bg-green-900 hover:bg-green-800');
        icon.removeClass('text-red-500').addClass('text-green-500');
        text.text('Profiling ON');
    } else {
        button.removeClass('bg-green-900 hover:bg-green-800').addClass('bg-red-900 hover:bg-red-800');
        icon.removeClass('text-green-500').addClass('text-red-500');
        text.text('Profiling OFF');
    }
}

function showToast(message, type = 'info') {
    const colors = {
        success: 'bg-green-500',
        error: 'bg-red-500',
        info: 'bg-blue-500'
    };
    
    const toast = $(`
        <div class="fixed bottom-4 right-4 ${colors[type]} text-white px-6 py-3 rounded-lg shadow-lg z-50">
            <i class="fas fa-${type === 'success' ? 'check-circle' : type === 'error' ? 'exclamation-circle' : 'info-circle'} mr-2"></i>
            ${message}
        </div>
    `);
    
    $('body').append(toast);
    
    setTimeout(() => {
        toast.fadeOut(300, function() {
            $(this).remove();
        });
    }, 3000);
}

// Loading overlay functions
function showLoadingOverlay(message = 'Loading...') {
    // Remove existing overlay if any
    $('#loading-overlay').remove();
    
    const overlay = $(`
        <div id="loading-overlay" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div class="bg-gray-800 rounded-lg p-6 flex flex-col items-center space-y-4">
                <div class="animate-spin rounded-full h-12 w-12 border-4 border-blue-500 border-t-transparent"></div>
                <div class="text-white text-lg font-medium">${message}</div>
            </div>
        </div>
    `);
    
    $('body').append(overlay);
}

function hideLoadingOverlay() {
    $('#loading-overlay').fadeOut(200, function() {
        $(this).remove();
    });
}
