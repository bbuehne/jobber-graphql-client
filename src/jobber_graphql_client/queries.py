"""GraphQL query definitions for Jobber API.

These queries are used by the MCP tools to fetch data from Jobber.
Reference: https://developer.getjobber.com/docs/graphql
"""

# ============================================================================
# CLIENT QUERIES
# ============================================================================

SEARCH_CLIENTS_QUERY = """
query SearchClients($limit: Int!, $searchTerm: String, $after: String) {
    clients(first: $limit, searchTerm: $searchTerm, after: $after) {
        edges {
            node {
                id
                firstName
                lastName
                companyName
                emails {
                    address
                    primary
                }
                phones {
                    number
                    primary
                }
                balance
            }
            cursor
        }
        pageInfo {
            hasNextPage
            endCursor
            startCursor
            hasPreviousPage
        }
        totalCount
    }
}
"""

GET_CLIENT_QUERY = """
query GetClient($id: EncodedId!) {
    client(id: $id) {
        id
        firstName
        lastName
        companyName
        emails {
            address
            primary
        }
        phones {
            number
            primary
        }
        properties {
            id
            address {
                street1
                city
                province
                postalCode
            }
        }
        balance
        createdAt
        updatedAt
    }
}
"""

LIST_CLIENTS_QUERY = """
query ListClients(
    $limit: Int!
    $after: String
    $filter: ClientFilterAttributes
    $searchTerm: String
    $sort: ClientsSortInput
) {
    clients(
        first: $limit
        after: $after
        filter: $filter
        searchTerm: $searchTerm
        sort: $sort
    ) {
        edges {
            node {
                id
                firstName
                lastName
                companyName
                isCompany
                isLead
                isArchived
                balance
                emails {
                    address
                    primary
                    description
                }
                phones {
                    number
                    primary
                    description
                }
                tags(first: 20) {
                    edges {
                        node {
                            id
                            label
                        }
                    }
                }
                createdAt
                updatedAt
            }
            cursor
        }
        pageInfo {
            hasNextPage
            endCursor
        }
        totalCount
    }
}
"""

FIND_SIMILAR_CLIENTS_QUERY = """
query FindSimilarClients(
    $name: String
    $companyName: String
    $emails: [String!]
    $limit: Int!
) {
    similarClients(
        name: $name
        companyName: $companyName
        emails: $emails
        first: $limit
    ) {
        edges {
            node {
                id
                firstName
                lastName
                companyName
                isCompany
                emails {
                    address
                    primary
                }
                phones {
                    number
                    primary
                }
                createdAt
                updatedAt
            }
            cursor
        }
        totalCount
    }
}
"""

GET_CLIENT_META_QUERY = """
query GetClientMeta($id: EncodedId!) {
    clientMeta(id: $id) {
        clientHub
        counts {
            deposits
            invoices
            jobs
            notes
            payments
            properties
            quotes
            requests
            tasks
            visits
        }
    }
    client(id: $id) {
        id
        firstName
        lastName
        companyName
        balance
        isLead
        isArchived
        updatedAt
    }
}
"""

SEARCH_CLIENT_EMAILS_QUERY = """
query SearchClientEmails($searchTerm: String, $limit: Int!) {
    clientEmails(searchTerm: $searchTerm, first: $limit) {
        edges {
            node {
                id
                address
                description
                primary
                client {
                    id
                    firstName
                    lastName
                    companyName
                }
            }
        }
        totalCount
    }
}
"""

SEARCH_CLIENT_PHONES_QUERY = """
query SearchClientPhones(
    $searchTerm: String
    $filter: ClientPhoneFilterAttributes
    $limit: Int!
) {
    clientPhones(
        searchTerm: $searchTerm
        filter: $filter
        first: $limit
    ) {
        edges {
            node {
                id
                number
                description
                primary
                smsAllowed
                smsStopped
                client {
                    id
                    firstName
                    lastName
                    companyName
                }
            }
        }
        totalCount
    }
}
"""

# ============================================================================
# CLIENT TAG QUERIES
# ============================================================================

GET_CLIENT_TAGS_QUERY = """
query GetClientTags($id: EncodedId!) {
    client(id: $id) {
        id
        firstName
        lastName
        companyName
        isCompany
        tags(first: 100) {
            edges {
                node {
                    id
                    label
                }
            }
            totalCount
        }
    }
}
"""

EDIT_CLIENT_TAGS_MUTATION = """
mutation EditClientTags($clientId: EncodedId!, $input: ClientEditInput!) {
    clientEdit(clientId: $clientId, input: $input) {
        client {
            id
            firstName
            lastName
            companyName
            tags(first: 100) {
                edges {
                    node {
                        id
                        label
                    }
                }
                totalCount
            }
        }
        userErrors {
            message
            path
        }
    }
}
"""

# ============================================================================
# JOB QUERIES
# ============================================================================

LIST_JOBS_QUERY = """
query ListJobs(
    $limit: Int!
    $after: String
    $filter: JobFilterAttributes
    $searchTerm: String
    $sort: [JobsSortInput!]
) {
    jobs(
        first: $limit
        after: $after
        filter: $filter
        searchTerm: $searchTerm
        sort: $sort
    ) {
        edges {
            node {
                id
                jobNumber
                title
                jobStatus
                client {
                    id
                    firstName
                    lastName
                    companyName
                }
                property {
                    id
                    address {
                        street1
                        city
                        province
                    }
                }
                visits(first: 5) {
                    edges {
                        node {
                            id
                            startAt
                            endAt
                        }
                    }
                }
                startAt
                endAt
                completedAt
                total
                createdAt
            }
            cursor
        }
        pageInfo {
            hasNextPage
            endCursor
        }
        totalCount
    }
}
"""

GET_JOB_QUERY = """
query GetJob($id: EncodedId!) {
    job(id: $id) {
        id
        jobNumber
        title
        jobStatus
        instructions
        client {
            id
            firstName
            lastName
        }
        property {
            id
            address {
                street1
                city
                province
            }
        }
        startAt
        endAt
        total
        createdAt
        updatedAt
    }
}
"""

SEARCH_JOBS_QUERY = """
query SearchJobs($searchTerm: String!, $limit: Int!) {
    jobs(searchTerm: $searchTerm, first: $limit) {
        edges {
            node {
                id
                jobNumber
                title
                jobStatus
                client {
                    id
                    firstName
                    lastName
                    companyName
                }
                property {
                    id
                    address {
                        street1
                        city
                    }
                }
                total
                createdAt
            }
            cursor
        }
        pageInfo {
            hasNextPage
            endCursor
        }
        totalCount
    }
}
"""

# ============================================================================
# JOB MUTATIONS
# ============================================================================

CREATE_JOB_NOTE_MUTATION = """
mutation CreateJobNote($jobId: EncodedId!, $input: JobCreateNoteInput!) {
    jobCreateNote(jobId: $jobId, input: $input) {
        note {
            id
            message
            pinned
            createdAt
            createdBy {
                ... on User {
                    id
                    name {
                        full
                    }
                }
            }
        }
        userErrors {
            message
            path
        }
    }
}
"""

# ============================================================================
# INVOICE QUERIES
# ============================================================================

LIST_INVOICES_QUERY = """
query ListInvoices(
    $limit: Int!
    $after: String
    $filter: InvoiceFilterAttributes
    $searchTerm: String
    $sort: [InvoiceSortInput!]
) {
    invoices(
        first: $limit
        after: $after
        filter: $filter
        searchTerm: $searchTerm
        sort: $sort
    ) {
        edges {
            node {
                id
                invoiceNumber
                invoiceStatus
                issuedDate
                dueDate
                subject
                createdAt
                updatedAt
                client {
                    id
                    firstName
                    lastName
                    companyName
                }
                amounts {
                    total
                    paymentsTotal
                    invoiceBalance
                }
            }
            cursor
        }
        pageInfo {
            hasNextPage
            hasPreviousPage
            startCursor
            endCursor
        }
        totalCount
    }
}
"""

GET_INVOICE_QUERY = """
query GetInvoice($id: ID!) {
    invoice(id: $id) {
        id
        invoiceNumber
        invoiceStatus
        issuedDate
        dueDate
        message
        subject
        client {
            id
            firstName
            lastName
        }
        amounts {
            total
            paymentsTotal
            invoiceBalance
            taxAmount
            discountAmount
        }
        createdAt
        updatedAt
    }
}
"""

SEARCH_INVOICES_QUERY = """
query SearchInvoices($searchTerm: String!, $limit: Int!) {
    invoices(searchTerm: $searchTerm, first: $limit) {
        edges {
            node {
                id
                invoiceNumber
                invoiceStatus
                subject
                issuedDate
                dueDate
                client {
                    id
                    firstName
                    lastName
                    companyName
                }
                amounts {
                    total
                    invoiceBalance
                }
            }
            cursor
        }
        pageInfo {
            hasNextPage
            endCursor
        }
        totalCount
    }
}
"""

# ============================================================================
# INVOICE MUTATIONS
# ============================================================================

CREATE_INVOICE_NOTE_MUTATION = """
mutation CreateInvoiceNote($invoiceId: EncodedId!, $input: InvoiceCreateNoteInput!) {
    invoiceCreateNote(invoiceId: $invoiceId, input: $input) {
        note {
            id
            message
            pinned
            createdAt
            createdBy {
                ... on User {
                    id
                    name {
                        full
                    }
                }
            }
        }
        userErrors {
            message
            path
        }
    }
}
"""

# ============================================================================
# REQUEST QUERIES
# ============================================================================

LIST_REQUESTS_QUERY = """
query ListRequests($limit: Int!, $after: String, $filter: RequestFilterAttributes) {
    requests(first: $limit, after: $after, filter: $filter) {
        edges {
            node {
                id
                title
                requestStatus
                client {
                    id
                    firstName
                    lastName
                }
                property {
                    id
                }
                createdAt
            }
            cursor
        }
        pageInfo {
            hasNextPage
            endCursor
        }
        totalCount
    }
}
"""

GET_REQUEST_QUERY = """
query GetRequest($id: EncodedId!) {
    request(id: $id) {
        id
        title
        requestStatus
        source
        isScheduled
        isArchivable
        jobberWebUri
        companyName
        contactName
        email
        phone
        client {
            id
            firstName
            lastName
            companyName
            emails { address primary }
            phones { number primary }
        }
        property {
            id
            address {
                street1
                street2
                city
                province
                postalCode
            }
        }
        referringClient {
            id
            firstName
            lastName
        }
        assessment {
            id
            title
            startAt
            endAt
        }
        jobs(first: 10) {
            edges {
                node {
                    id
                    jobNumber
                    title
                    jobStatus
                }
            }
            totalCount
        }
        quotes(first: 10) {
            edges {
                node {
                    id
                    quoteNumber
                    title
                    quoteStatus
                }
            }
            totalCount
        }
        notes(first: 20) {
            edges {
                node {
                    ... on RequestNote {
                        id
                        message
                        pinned
                        createdAt
                        createdBy {
                            ... on User {
                                id
                                name { full }
                            }
                        }
                    }
                }
            }
            totalCount
        }
        createdAt
        updatedAt
    }
}
"""

SEARCH_REQUESTS_QUERY = """
query SearchRequests($searchTerm: String!, $limit: Int!, $after: String) {
    requests(searchTerm: $searchTerm, first: $limit, after: $after) {
        edges {
            node {
                id
                title
                requestStatus
                source
                isScheduled
                client {
                    id
                    firstName
                    lastName
                    companyName
                }
                property {
                    id
                    address {
                        street1
                        city
                    }
                }
                createdAt
            }
            cursor
        }
        pageInfo {
            hasNextPage
            endCursor
        }
        totalCount
    }
}
"""

LIST_REQUESTS_ENHANCED_QUERY = """
query ListRequestsEnhanced(
    $limit: Int!
    $after: String
    $filter: RequestFilterAttributes
    $searchTerm: String
    $sort: RequestsSortInput
) {
    requests(
        first: $limit
        after: $after
        filter: $filter
        searchTerm: $searchTerm
        sort: $sort
    ) {
        edges {
            node {
                id
                title
                requestStatus
                source
                isScheduled
                isArchivable
                companyName
                contactName
                email
                phone
                client {
                    id
                    firstName
                    lastName
                    companyName
                }
                property {
                    id
                    address {
                        street1
                        city
                        province
                    }
                }
                assessment {
                    id
                    startAt
                }
                createdAt
                updatedAt
            }
            cursor
        }
        pageInfo {
            hasNextPage
            endCursor
        }
        totalCount
    }
}
"""

# Request mutations
EDIT_REQUEST_MUTATION = """
mutation EditRequest($requestId: EncodedId!, $input: RequestEditInput!) {
    requestEdit(requestId: $requestId, input: $input) {
        request {
            id
            title
            requestStatus
            property {
                id
                address { street1 city }
            }
            referringClient {
                id
                firstName
                lastName
            }
        }
        userErrors {
            message
            path
        }
    }
}
"""

ARCHIVE_REQUEST_MUTATION = """
mutation ArchiveRequest($requestId: EncodedId!) {
    requestArchive(requestId: $requestId) {
        request {
            id
            title
            requestStatus
        }
        userErrors {
            message
            path
        }
    }
}
"""

UNARCHIVE_REQUEST_MUTATION = """
mutation UnarchiveRequest($requestId: EncodedId!) {
    requestUnarchive(requestId: $requestId) {
        request {
            id
            title
            requestStatus
        }
        userErrors {
            message
            path
        }
    }
}
"""

CREATE_REQUEST_NOTE_MUTATION = """
mutation CreateRequestNote($requestId: EncodedId!, $input: RequestCreateNoteInput!) {
    requestCreateNote(requestId: $requestId, input: $input) {
        request {
            id
            title
        }
        requestNote {
            id
            message
            pinned
            createdAt
            createdBy {
                ... on User {
                    id
                    name { full }
                }
            }
        }
        userErrors {
            message
            path
        }
    }
}
"""

# ============================================================================
# VISIT QUERIES
# ============================================================================

LIST_VISITS_QUERY = """
query ListVisits($limit: Int!, $after: String, $filter: VisitFilterAttributes) {
    visits(first: $limit, after: $after, filter: $filter) {
        edges {
            node {
                id
                title
                job {
                    id
                    jobNumber
                }
                startAt
                endAt
                assignedUsers(first: 10) {
                    edges {
                        node {
                            id
                            name {
                                full
                            }
                        }
                    }
                }
            }
            cursor
        }
        pageInfo {
            hasNextPage
            endCursor
        }
        totalCount
    }
}
"""

GET_VISIT_QUERY = """
query GetVisit($id: EncodedId!) {
    visit(id: $id) {
        id
        title
        job {
            id
            jobNumber
        }
        startAt
        endAt
        assignedUsers(first: 10) {
            edges {
                node {
                    id
                    name {
                        full
                    }
                }
            }
        }
        createdAt
        isComplete
        instructions
    }
}
"""

# ============================================================================
# TEAM MEMBER / USER QUERIES
# ============================================================================

LIST_TEAM_MEMBERS_QUERY = """
query ListTeamMembers($limit: Int!, $after: String, $filter: UsersFilterAttributes) {
    users(first: $limit, after: $after, filter: $filter) {
        edges {
            node {
                id
                name {
                    first
                    last
                    full
                }
                email {
                    raw
                    isValid
                }
                phone {
                    friendly
                    raw
                }
                status
                isAccountAdmin
                isAccountOwner
                isCurrentUser
                availableForScheduling
                assignedColor
                createdAt
                lastLoginAt
            }
            cursor
        }
        pageInfo {
            hasNextPage
            endCursor
        }
        totalCount
    }
}
"""

GET_USER_QUERY = """
query GetUser($id: EncodedId) {
    user(id: $id) {
        id
        name {
            first
            last
            full
        }
        email {
            raw
            isValid
        }
        phone {
            friendly
            raw
            areaCode
            countryCode
        }
        status
        isAccountAdmin
        isAccountOwner
        isCurrentUser
        availableForScheduling
        assignedColor
        createdAt
        lastLoginAt
        timezone
        firstDayOfTheWeek
        address {
            street1
            street2
            city
            province
            postalCode
            country
        }
        assignedVehicle {
            id
            licensePlate
            make
            model
            year
        }
    }
}
"""

GET_USER_SCHEDULE_QUERY = """
query GetUserSchedule($limit: Int!, $after: String, $filter: VisitFilterAttributes) {
    visits(first: $limit, after: $after, filter: $filter) {
        edges {
            node {
                id
                title
                instructions
                startAt
                endAt
                isComplete
                visitStatus
                job {
                    id
                    jobNumber
                    title
                }
                client {
                    id
                    firstName
                    lastName
                    companyName
                }
                property {
                    id
                    address {
                        street1
                        city
                        province
                    }
                }
                assignedUsers(first: 10) {
                    edges {
                        node {
                            id
                            name {
                                full
                            }
                        }
                    }
                }
            }
            cursor
        }
        pageInfo {
            hasNextPage
            endCursor
        }
        totalCount
    }
}
"""

EDIT_USER_MUTATION = """
mutation EditUser($userId: EncodedId!, $input: UserEditInput!) {
    userEdit(userId: $userId, input: $input) {
        user {
            id
            name {
                first
                last
                full
            }
            email {
                raw
            }
            status
        }
        userErrors {
            message
            path
        }
    }
}
"""

# ============================================================================
# QUOTE QUERIES
# ============================================================================

LIST_QUOTES_QUERY = """
query ListQuotes($limit: Int!, $after: String, $filter: QuoteFilterAttributes, $sort: [QuotesSortInput!]) {
    quotes(first: $limit, after: $after, filter: $filter, sort: $sort) {
        edges {
            node {
                id
                quoteNumber
                title
                quoteStatus
                createdAt
                updatedAt
                sentAt
                client {
                    id
                    firstName
                    lastName
                    companyName
                }
                property {
                    id
                    address {
                        street1
                        city
                        province
                    }
                }
                amounts {
                    subtotal
                    taxAmount
                    total
                    depositAmount
                    discountAmount
                    outstandingDepositAmount
                }
            }
            cursor
        }
        pageInfo {
            hasNextPage
            endCursor
        }
        totalCount
    }
}
"""

GET_QUOTE_QUERY = """
query GetQuote($id: EncodedId!) {
    quote(id: $id) {
        id
        quoteNumber
        title
        message
        quoteStatus
        createdAt
        updatedAt
        sentAt
        transitionedAt
        contractDisclaimer
        clientHubUri
        clientHubViewedAt
        jobberWebUri

        client {
            id
            firstName
            lastName
            companyName
            emails {
                address
                primary
            }
            phones {
                number
                primary
            }
        }

        property {
            id
            address {
                street1
                street2
                city
                province
                postalCode
            }
        }

        request {
            id
            title
            requestStatus
        }

        salesperson {
            id
            name {
                full
            }
            email {
                raw
            }
        }

        amounts {
            subtotal
            taxAmount
            total
            discountAmount
            depositAmount
            outstandingDepositAmount
            nonTaxAmount
        }


        lineItems(first: 100) {
            edges {
                node {
                    id
                    name
                    description
                    quantity
                    unitPrice
                    totalPrice
                    taxable
                    optional
                    recommended
                    sortOrder
                    textOnly
                }
            }
            totalCount
        }

        notes(first: 50) {
            edges {
                node {
                    ... on QuoteNote {
                        id
                        message
                        createdAt
                        createdBy {
                            ... on User {
                                id
                                name {
                                    full
                                }
                            }
                        }
                        pinned
                    }
                }
            }
        }

        jobs(first: 10) {
            edges {
                node {
                    id
                    jobNumber
                    title
                    jobStatus
                }
            }
        }

        depositRecords(first: 10) {
            edges {
                node {
                    id
                    amount
                    entryDate
                }
            }
        }

        lastTransitioned {
            approvedAt
            changesRequestedAt
            convertedAt
        }
    }
}
"""

SEARCH_QUOTES_QUERY = """
query SearchQuotes($searchTerm: String!, $limit: Int!, $after: String) {
    quotes(searchTerm: $searchTerm, first: $limit, after: $after) {
        edges {
            node {
                id
                quoteNumber
                title
                quoteStatus
                createdAt
                sentAt
                client {
                    id
                    firstName
                    lastName
                    companyName
                }
                property {
                    id
                    address {
                        street1
                        city
                    }
                }
                amounts {
                    total
                }
            }
            cursor
        }
        pageInfo {
            hasNextPage
            endCursor
        }
        totalCount
    }
}
"""

LIST_QUOTES_BY_STATUS_QUERY = """
query ListQuotesByStatus($status: QuoteStatusTypeEnum!, $limit: Int!, $after: String) {
    quotes(
        first: $limit,
        after: $after,
        filter: { status: $status },
        sort: [{ key: CREATED_AT, direction: DESCENDING }]
    ) {
        edges {
            node {
                id
                quoteNumber
                title
                quoteStatus
                createdAt
                sentAt
                transitionedAt
                client {
                    id
                    firstName
                    lastName
                    companyName
                }
                property {
                    id
                    address {
                        street1
                        city
                    }
                }
                amounts {
                    total
                    depositAmount
                    outstandingDepositAmount
                }
                lastTransitioned {
                    approvedAt
                    changesRequestedAt
                    convertedAt
                }
            }
            cursor
        }
        pageInfo {
            hasNextPage
            endCursor
        }
        totalCount
    }
}
"""

FIND_OVERDUE_QUOTES_QUERY = """
query FindOverdueQuotes($limit: Int!, $sentBefore: Iso8601DateTimeRangeInput!, $after: String) {
    quotes(
        first: $limit,
        after: $after,
        filter: {
            status: awaiting_response,
            sentAt: $sentBefore
        },
        sort: [{ key: LAST_SENT_AT, direction: ASCENDING }]
    ) {
        edges {
            node {
                id
                quoteNumber
                title
                quoteStatus
                sentAt
                createdAt
                clientHubViewedAt
                client {
                    id
                    firstName
                    lastName
                    companyName
                }
                amounts {
                    total
                }
            }
            cursor
        }
        pageInfo {
            hasNextPage
            endCursor
        }
        totalCount
    }
}
"""

GET_QUOTE_PROSPECTS_QUERY = """
query GetQuoteProspects($limit: Int!, $after: String) {
    quotes(
        first: $limit,
        after: $after,
        filter: { status: awaiting_response },
        sort: [{ key: LAST_SENT_AT, direction: DESCENDING }]
    ) {
        edges {
            node {
                id
                quoteNumber
                title
                quoteStatus
                sentAt
                clientHubViewedAt
                client {
                    id
                    firstName
                    lastName
                    companyName
                }
                property {
                    id
                    address {
                        street1
                        city
                    }
                }
                amounts {
                    total
                    depositAmount
                }
                lastTransitioned {
                    approvedAt
                }
            }
            cursor
        }
        pageInfo {
            hasNextPage
            endCursor
        }
        totalCount
    }
}
"""

QUOTE_FINANCIAL_SUMMARY_QUERY = """
query QuoteFinancialSummary($limit: Int!, $filter: QuoteFilterAttributes, $after: String) {
    quotes(first: $limit, filter: $filter, after: $after) {
        edges {
            node {
                id
                quoteStatus
                amounts {
                    total
                    depositAmount
                    outstandingDepositAmount
                }
                lastTransitioned {
                    convertedAt
                }
            }
            cursor
        }
        pageInfo {
            hasNextPage
            endCursor
        }
        totalCount
    }
}
"""

FIND_QUOTES_MISSING_SALESPERSON_QUERY = """
query FindQuotesMissingSalesperson(
    $limit: Int!
    $after: String
    $filter: QuoteFilterAttributes
    $sort: [QuotesSortInput!]
) {
    quotes(first: $limit, after: $after, filter: $filter, sort: $sort) {
        edges {
            node {
                id
                quoteNumber
                title
                quoteStatus
                createdAt
                updatedAt
                client {
                    id
                    firstName
                    lastName
                    companyName
                }
                amounts {
                    total
                }
                salesperson {
                    id
                    name {
                        full
                    }
                }
                jobs(first: 10) {
                    edges {
                        node {
                            id
                            jobNumber
                        }
                    }
                }
                lastTransitioned {
                    convertedAt
                }
            }
            cursor
        }
        pageInfo {
            hasNextPage
            endCursor
        }
        totalCount
    }
}
"""

# ============================================================================
# MUTATION QUERIES
# ============================================================================

# Note: CREATE_CLIENT_MUTATION is defined later with more complete return fields

CREATE_REQUEST_MUTATION = """
mutation CreateRequest($input: RequestCreateInput!) {
    requestCreate(input: $input) {
        request {
            id
            title
            requestStatus
        }
        userErrors {
            message
            path
        }
    }
}
"""

CREATE_JOB_MUTATION = """
mutation CreateJob($input: JobCreateAttributes!) {
    jobCreate(input: $input) {
        job {
            id
            jobNumber
            title
        }
        userErrors {
            message
            path
        }
    }
}
"""

# Note: CREATE_VISIT_MUTATION is defined later with correct EncodedId type and more return fields

EDIT_VISIT_MUTATION = """
mutation EditVisit($id: ID!, $attributes: VisitEditAttributes!) {
    visitEdit(id: $id, attributes: $attributes) {
        visit {
            id
            title
            startAt
            endAt
        }
        userErrors {
            message
            path
        }
    }
}
"""

CREATE_ASSESSMENT_MUTATION = """
mutation CreateAssessment($requestId: EncodedId!, $input: AssessmentCreateInput!) {
    assessmentCreate(requestId: $requestId, input: $input) {
        assessment {
            id
            title
            startAt
            endAt
            instructions
        }
        userErrors {
            message
            path
        }
    }
}
"""

CREATE_PROPERTY_MUTATION = """
mutation CreateProperty($clientId: EncodedId!, $input: PropertyCreateInput!) {
    propertyCreate(clientId: $clientId, input: $input) {
        client {
            id
            firstName
            lastName
            companyName
        }
        properties {
            id
            name
            address {
                street1
                street2
                city
                province
                postalCode
                country
            }
            isBillingAddress
        }
        userErrors {
            message
            path
        }
    }
}
"""

# ============================================================================
# PROPERTY QUERIES
# ============================================================================

LIST_PROPERTIES_QUERY = """
query ListProperties(
    $limit: Int!
    $after: String
    $filter: PropertiesFilterAttributes
    $searchTerm: String
) {
    properties(
        first: $limit
        after: $after
        filter: $filter
        searchTerm: $searchTerm
    ) {
        edges {
            node {
                id
                name
                address {
                    street1
                    street2
                    city
                    province
                    postalCode
                    country
                }
                isBillingAddress
                client {
                    id
                    firstName
                    lastName
                    companyName
                }
            }
            cursor
        }
        pageInfo {
            hasNextPage
            endCursor
        }
        totalCount
    }
}
"""

GET_PROPERTY_QUERY = """
query GetProperty($id: EncodedId!) {
    property(id: $id) {
        id
        name
        address {
            street1
            street2
            city
            province
            postalCode
            country
        }
        isBillingAddress
        routingOrder
        client {
            id
            firstName
            lastName
            companyName
            emails {
                address
                primary
            }
            phones {
                number
                primary
            }
        }
        contacts(first: 10) {
            edges {
                node {
                    id
                    firstName
                    lastName
                    email
                    phone
                }
            }
            totalCount
        }
        jobs(first: 10) {
            edges {
                node {
                    id
                    jobNumber
                    title
                    jobStatus
                }
            }
            totalCount
        }
        quotes(first: 10) {
            edges {
                node {
                    id
                    quoteNumber
                    title
                    quoteStatus
                }
            }
            totalCount
        }
        requests(first: 10) {
            edges {
                node {
                    id
                    title
                    requestStatus
                }
            }
            totalCount
        }
    }
}
"""

EDIT_PROPERTY_MUTATION = """
mutation EditProperty($propertyId: EncodedId!, $input: PropertyEditInput!) {
    propertyEdit(propertyId: $propertyId, input: $input) {
        property {
            id
            name
            address {
                street1
                street2
                city
                province
                postalCode
                country
            }
            isBillingAddress
        }
        userErrors {
            message
            path
        }
    }
}
"""

CREATE_CLIENT_NOTE_MUTATION = """
mutation CreateClientNote($clientId: EncodedId!, $input: ClientCreateNoteInput!) {
    clientCreateNote(clientId: $clientId, input: $input) {
        clientNote {
            id
            message
            pinned
            createdAt
            createdBy {
                ... on User {
                    id
                    name {
                        full
                    }
                }
            }
        }
        userErrors {
            message
            path
        }
    }
}
"""

# ============================================================================
# VISIT MUTATIONS
# ============================================================================

CREATE_VISIT_MUTATION = """
mutation CreateVisit($jobId: EncodedId!, $input: VisitCreateInput!) {
    visitCreate(jobId: $jobId, input: $input) {
        visit {
            id
            title
            instructions
            startAt
            endAt
            job {
                id
                jobNumber
            }
            client {
                id
                firstName
                lastName
            }
            assignedUsers(first: 10) {
                edges {
                    node {
                        id
                        name {
                            full
                        }
                    }
                }
            }
        }
        userErrors {
            message
            path
        }
    }
}
"""

UPDATE_VISIT_MUTATION = """
mutation UpdateVisit($id: EncodedId!, $attributes: VisitEditAttributes!) {
    visitEdit(id: $id, attributes: $attributes) {
        visit {
            id
            title
            instructions
            startAt
            endAt
        }
        userErrors {
            message
            path
        }
    }
}
"""

UPDATE_VISIT_SCHEDULE_MUTATION = """
mutation UpdateVisitSchedule($visitId: EncodedId!, $input: VisitEditScheduleInput!) {
    visitEditSchedule(id: $visitId, input: $input) {
        visit {
            id
            title
            startAt
            endAt
            job {
                id
                jobNumber
            }
            client {
                id
                firstName
                lastName
            }
        }
        userErrors {
            message
            path
        }
    }
}
"""

ASSIGN_VISIT_USERS_MUTATION = """
mutation AssignVisitUsers($visitId: EncodedId!, $input: VisitEditAssignedUsersInput!) {
    visitEditAssignedUsers(visitId: $visitId, input: $input) {
        visit {
            id
            title
            assignedUsers(first: 10) {
                edges {
                    node {
                        id
                        name {
                            full
                        }
                    }
                }
            }
        }
        userErrors {
            message
            path
        }
    }
}
"""

COMPLETE_VISIT_MUTATION = """
mutation CompleteVisit($visitId: EncodedId!) {
    visitComplete(visitId: $visitId) {
        visit {
            id
            title
            isComplete
            completedAt
            completedBy
            job {
                id
                jobNumber
            }
        }
        userErrors {
            message
            path
        }
    }
}
"""

DELETE_VISIT_MUTATION = """
mutation DeleteVisit($visitIds: [EncodedId!]!) {
    visitDelete(visitIds: $visitIds) {
        success
        userErrors {
            message
            path
        }
    }
}
"""

SEARCH_VISITS_QUERY = """
query SearchVisits(
    $limit: Int!
    $after: String
    $filter: VisitFilterAttributes
) {
    visits(
        first: $limit
        after: $after
        filter: $filter
    ) {
        edges {
            node {
                id
                title
                instructions
                startAt
                endAt
                isComplete
                completedAt
                visitStatus
                job {
                    id
                    jobNumber
                    title
                }
                client {
                    id
                    firstName
                    lastName
                    companyName
                }
                property {
                    id
                    address {
                        street1
                        city
                        province
                    }
                }
                assignedUsers(first: 10) {
                    edges {
                        node {
                            id
                            name {
                                full
                            }
                        }
                    }
                }
            }
            cursor
        }
        pageInfo {
            hasNextPage
            endCursor
        }
        totalCount
    }
}
"""

# ============================================================================
# TASK QUERIES
# ============================================================================

LIST_TASKS_QUERY = """
query ListTasks(
    $limit: Int!
    $after: String
    $filter: TaskFilterAttributes
    $sort: [TaskSortInput!]
) {
    tasks(
        first: $limit
        after: $after
        filter: $filter
        sort: $sort
    ) {
        edges {
            node {
                id
                title
                instructions
                startAt
                endAt
                allDay
                isComplete
                isRecurring
                duration
                client {
                    id
                    firstName
                    lastName
                    companyName
                }
                property {
                    id
                    address {
                        street1
                        city
                        province
                    }
                }
                assignedUsers(first: 10) {
                    edges {
                        node {
                            id
                            name {
                                full
                            }
                        }
                    }
                }
                createdBy {
                    ... on User {
                        id
                        name {
                            full
                        }
                    }
                }
            }
            cursor
        }
        pageInfo {
            hasNextPage
            endCursor
        }
        totalCount
    }
}
"""

GET_TASK_QUERY = """
query GetTask($id: EncodedId!) {
    task(id: $id) {
        id
        title
        instructions
        startAt
        endAt
        allDay
        isComplete
        isRecurring
        isDefaultTitle
        duration
        teamReminderOffset
        routingOrder
        overrideOrder
        client {
            id
            firstName
            lastName
            companyName
            emails {
                address
                primary
            }
            phones {
                number
                primary
            }
        }
        property {
            id
            name
            address {
                street1
                street2
                city
                province
                postalCode
            }
        }
        assignedUsers(first: 20) {
            edges {
                node {
                    id
                    name {
                        full
                    }
                    email {
                        raw
                    }
                }
            }
            totalCount
        }
        createdBy {
            ... on User {
                id
                name {
                    full
                }
            }
        }
        recurrenceSchedule {
            rule
            humanReadableRule
        }
    }
}
"""

# ============================================================================
# TASK MUTATIONS
# ============================================================================

CREATE_TASK_MUTATION = """
mutation CreateTask($clientId: EncodedId, $propertyId: EncodedId, $input: TaskCreateInput!) {
    taskCreate(clientId: $clientId, propertyId: $propertyId, input: $input) {
        task {
            id
            title
            instructions
            startAt
            endAt
            allDay
            isComplete
            isRecurring
            client {
                id
                firstName
                lastName
            }
            property {
                id
                address {
                    street1
                    city
                }
            }
            assignedUsers(first: 10) {
                edges {
                    node {
                        id
                        name {
                            full
                        }
                    }
                }
            }
        }
        userErrors {
            message
            path
        }
    }
}
"""

EDIT_TASK_MUTATION = """
mutation EditTask($taskId: EncodedId!, $input: TaskEditInput!) {
    taskEdit(taskId: $taskId, input: $input) {
        task {
            id
            title
            instructions
            startAt
            endAt
            allDay
            isComplete
            isRecurring
            client {
                id
                firstName
                lastName
            }
            property {
                id
                address {
                    street1
                    city
                }
            }
            assignedUsers(first: 10) {
                edges {
                    node {
                        id
                        name {
                            full
                        }
                    }
                }
            }
        }
        userErrors {
            message
            path
        }
    }
}
"""

DELETE_TASK_MUTATION = """
mutation DeleteTask($taskIds: [EncodedId!]!, $deleteFutureRecurring: Boolean) {
    taskDelete(taskIds: $taskIds, deleteFutureRecurring: $deleteFutureRecurring) {
        deletedTasks
        userErrors {
            message
            path
        }
    }
}
"""

# ============================================================================
# PRODUCT/SERVICE QUERIES
# ============================================================================

LIST_PRODUCTS_QUERY = """
query ListProducts(
    $limit: Int!
    $after: String
    $filter: ProductsFilterInput
    $searchTerm: String
) {
    products(
        first: $limit
        after: $after
        filter: $filter
        searchTerm: $searchTerm
    ) {
        edges {
            node {
                id
                name
                description
                category
                defaultUnitCost
                internalUnitCost
                markup
                taxable
                visible
                durationMinutes
                onlineBookingsEnabled
            }
            cursor
        }
        pageInfo {
            hasNextPage
            endCursor
        }
        totalCount
    }
}
"""

GET_PRODUCT_QUERY = """
query GetProduct($id: EncodedId!) {
    product(id: $id) {
        id
        name
        description
        category
        defaultUnitCost
        internalUnitCost
        markup
        taxable
        visible
        durationMinutes
        onlineBookingsEnabled
        bookableType
        quantityRange {
            min
            max
        }
    }
}
"""

# ============================================================================
# PRODUCT/SERVICE MUTATIONS
# ============================================================================

CREATE_PRODUCT_MUTATION = """
mutation CreateProduct($input: ProductsAndServicesInput!) {
    productsAndServicesCreate(input: $input) {
        productOrService {
            id
            name
            description
            category
            defaultUnitCost
            internalUnitCost
            taxable
            visible
        }
        userErrors {
            message
            path
        }
    }
}
"""

UPDATE_PRODUCT_MUTATION = """
mutation UpdateProduct($productOrServiceId: EncodedId!, $input: ProductsAndServicesEditInput!) {
    productsAndServicesEdit(productOrServiceId: $productOrServiceId, input: $input) {
        productOrService {
            id
            name
            description
            category
            defaultUnitCost
            internalUnitCost
            taxable
            visible
            markup
            durationMinutes
        }
        userErrors {
            message
            path
        }
    }
}
"""

# ============================================================================
# PAYMENT RECORD QUERIES (Read-Only)
# ============================================================================

LIST_PAYMENT_RECORDS_QUERY = """
query ListPaymentRecords(
    $limit: Int!
    $after: String
    $filter: PaymentRecordFilterAttributes
    $sort: PaymentRecordSortAttributes
) {
    paymentRecords(
        first: $limit
        after: $after
        filter: $filter
        sort: $sort
    ) {
        edges {
            node {
                id
                amount
                entryDate
                adjustmentType
                paymentType
                details
                canEdit
                paymentOrigin
                sentAt
                client {
                    id
                    firstName
                    lastName
                    companyName
                }
                invoice {
                    id
                    invoiceNumber
                    subject
                }
                quote {
                    id
                    quoteNumber
                    title
                }
            }
            cursor
        }
        pageInfo {
            hasNextPage
            endCursor
        }
        totalCount
    }
}
"""

GET_PAYMENT_RECORD_QUERY = """
query GetPaymentRecord($id: EncodedId!) {
    paymentRecord(id: $id) {
        id
        amount
        entryDate
        adjustmentType
        paymentType
        details
        canEdit
        paymentOrigin
        sentAt
        tipAmount
        jobberPaymentLast4
        jobberPaymentPaymentMethod
        jobberPaymentTransactionStatus
        client {
            id
            firstName
            lastName
            companyName
            emails {
                address
                primary
            }
            phones {
                number
                primary
            }
        }
        invoice {
            id
            invoiceNumber
            subject
            invoiceStatus
            amounts {
                total
                invoiceBalance
            }
        }
        quote {
            id
            quoteNumber
            title
            quoteStatus
        }
        allocations(first: 10) {
            edges {
                node {
                    amount
                }
            }
            totalCount
        }
        refunds(first: 10) {
            edges {
                node {
                    id
                    amount
                    entryDate
                }
            }
            totalCount
        }
    }
}
"""

GET_INVOICE_PAYMENTS_QUERY = """
query GetInvoicePayments($invoiceId: ID!, $limit: Int!, $after: String) {
    invoice(id: $invoiceId) {
        id
        invoiceNumber
        subject
        invoiceStatus
        amounts {
            total
            paymentsTotal
            invoiceBalance
        }
        paymentRecords(first: $limit, after: $after) {
            edges {
                node {
                    id
                    amount
                    entryDate
                    adjustmentType
                    paymentType
                    details
                    paymentOrigin
                    tipAmount
                }
                cursor
            }
            pageInfo {
                hasNextPage
                endCursor
            }
            totalCount
        }
    }
}
"""

GET_JOB_PAYMENTS_QUERY = """
query GetJobPayments($jobId: ID!, $limit: Int!, $after: String) {
    job(id: $jobId) {
        id
        jobNumber
        title
        jobStatus
        total
        paymentRecords(first: $limit, after: $after) {
            edges {
                node {
                    id
                    amount
                    entryDate
                    adjustmentType
                    paymentType
                    details
                }
                cursor
            }
            pageInfo {
                hasNextPage
                endCursor
            }
            totalCount
        }
    }
}
"""

# ============================================================================
# TIMESHEET ENTRY QUERIES (Read-Only)
# ============================================================================

LIST_TIMESHEET_ENTRIES_QUERY = """
query ListTimesheetEntries(
    $limit: Int!
    $after: String
    $filter: TimeSheetEntriesFilterAttributes
    $sort: [TimeSheetEntriesSortAttributes!]
) {
    timeSheetEntries(
        first: $limit
        after: $after
        filter: $filter
        sort: $sort
    ) {
        edges {
            node {
                id
                startAt
                endAt
                duration
                note
                isApproved
                isRunning
                user {
                    id
                    name {
                        full
                    }
                }
                job {
                    id
                    jobNumber
                    title
                }
                visit {
                    id
                    title
                }
                client {
                    id
                    firstName
                    lastName
                    companyName
                }
            }
            cursor
        }
        pageInfo {
            hasNextPage
            endCursor
        }
        totalCount
    }
}
"""

GET_TIMESHEET_ENTRY_QUERY = """
query GetTimesheetEntry($id: EncodedId!) {
    timeSheetEntry(id: $id) {
        id
        startAt
        endAt
        duration
        note
        isApproved
        isRunning
        user {
            id
            name {
                first
                last
                full
            }
            email {
                raw
            }
        }
        job {
            id
            jobNumber
            title
            jobStatus
            client {
                id
                firstName
                lastName
                companyName
            }
        }
        visit {
            id
            title
            startAt
            endAt
            property {
                id
                address {
                    street1
                    city
                    province
                }
            }
        }
        client {
            id
            firstName
            lastName
            companyName
        }
        createdAt
        updatedAt
    }
}
"""

GET_JOB_TIMESHEETS_QUERY = """
query GetJobTimesheets($jobId: ID!, $limit: Int!, $after: String) {
    job(id: $jobId) {
        id
        jobNumber
        title
        jobStatus
        client {
            id
            firstName
            lastName
            companyName
        }
        timeSheetEntries(first: $limit, after: $after) {
            edges {
                node {
                    id
                    startAt
                    endAt
                    duration
                    note
                    isApproved
                    isRunning
                    user {
                        id
                        name {
                            full
                        }
                    }
                    visit {
                        id
                        title
                    }
                }
                cursor
            }
            pageInfo {
                hasNextPage
                endCursor
            }
            totalCount
        }
    }
}
"""

GET_VISIT_TIMESHEETS_QUERY = """
query GetVisitTimesheets($visitId: ID!, $limit: Int!, $after: String) {
    visit(id: $visitId) {
        id
        title
        startAt
        endAt
        job {
            id
            jobNumber
            title
        }
        client {
            id
            firstName
            lastName
            companyName
        }
        timeSheetEntries(first: $limit, after: $after) {
            edges {
                node {
                    id
                    startAt
                    endAt
                    duration
                    note
                    isApproved
                    isRunning
                    user {
                        id
                        name {
                            full
                        }
                    }
                }
                cursor
            }
            pageInfo {
                hasNextPage
                endCursor
            }
            totalCount
        }
    }
}
"""

# ============================================================================
# QUOTE MUTATIONS
# ============================================================================

CREATE_QUOTE_MUTATION = """
mutation CreateQuote($attributes: QuoteCreateAttributes!) {
    quoteCreate(attributes: $attributes) {
        quote {
            id
            quoteNumber
            title
            quoteStatus
            message
            createdAt
            client {
                id
                firstName
                lastName
                companyName
            }
            property {
                id
                address {
                    street1
                    city
                    province
                }
            }
            amounts {
                subtotal
                taxAmount
                total
                depositAmount
                discountAmount
            }
            lineItems(first: 20) {
                edges {
                    node {
                        id
                        name
                        quantity
                        unitPrice
                        totalPrice
                    }
                }
                totalCount
            }
        }
        userErrors {
            message
            path
        }
    }
}
"""

EDIT_QUOTE_MUTATION = """
mutation EditQuote($quoteId: EncodedId!, $attributes: QuoteEditAttributes!) {
    quoteEdit(quoteId: $quoteId, attributes: $attributes) {
        quote {
            id
            quoteNumber
            title
            quoteStatus
            message
            contractDisclaimer
            updatedAt
            amounts {
                subtotal
                taxAmount
                total
                depositAmount
                discountAmount
            }
            salesperson {
                id
                name {
                    full
                }
            }
        }
        userErrors {
            message
            path
        }
    }
}
"""

CREATE_QUOTE_LINE_ITEMS_MUTATION = """
mutation CreateQuoteLineItems($quoteId: EncodedId!, $lineItems: [QuoteCreateLineItemAttributes!]!) {
    quoteCreateLineItems(quoteId: $quoteId, lineItems: $lineItems) {
        quote {
            id
            quoteNumber
            amounts {
                subtotal
                taxAmount
                total
            }
            lineItems(first: 50) {
                edges {
                    node {
                        id
                        name
                        description
                        quantity
                        unitPrice
                        totalPrice
                        taxable
                        optional
                        sortOrder
                    }
                }
                totalCount
            }
        }
        createdLineItems {
            id
            name
            description
            quantity
            unitPrice
            totalPrice
            taxable
            optional
        }
        userErrors {
            message
            path
        }
    }
}
"""

EDIT_QUOTE_LINE_ITEMS_MUTATION = """
mutation EditQuoteLineItems($quoteId: EncodedId!, $lineItems: [QuoteEditLineItemAttributes!]!) {
    quoteEditLineItems(quoteId: $quoteId, lineItems: $lineItems) {
        quote {
            id
            quoteNumber
            amounts {
                subtotal
                taxAmount
                total
            }
        }
        modifiedLineItems {
            id
            name
            description
            quantity
            unitPrice
            totalPrice
            taxable
            optional
        }
        userErrors {
            message
            path
        }
    }
}
"""

DELETE_QUOTE_LINE_ITEMS_MUTATION = """
mutation DeleteQuoteLineItems($quoteId: EncodedId!, $lineItemIds: [EncodedId!]!) {
    quoteDeleteLineItems(quoteId: $quoteId, lineItemIds: $lineItemIds) {
        quote {
            id
            quoteNumber
            amounts {
                subtotal
                taxAmount
                total
            }
            lineItems(first: 50) {
                edges {
                    node {
                        id
                        name
                        totalPrice
                    }
                }
                totalCount
            }
        }
        deletedLineItems {
            id
            name
        }
        userErrors {
            message
            path
        }
    }
}
"""

CREATE_QUOTE_NOTE_MUTATION = """
mutation CreateQuoteNote($quoteId: EncodedId!, $input: QuoteCreateNoteInput!) {
    quoteCreateNote(quoteId: $quoteId, input: $input) {
        quote {
            id
            quoteNumber
            title
        }
        note {
            id
            message
            pinned
            createdAt
            createdBy {
                ... on User {
                    id
                    name {
                        full
                    }
                }
            }
        }
        userErrors {
            message
            path
        }
    }
}
"""

# ============================================================================
# JOB MUTATIONS (Extended)
# ============================================================================

CREATE_JOB_FULL_MUTATION = """
mutation CreateJob($input: JobCreateAttributes!) {
    jobCreate(input: $input) {
        job {
            id
            jobNumber
            title
            jobStatus
            instructions
            createdAt
            client {
                id
                firstName
                lastName
                companyName
            }
            property {
                id
                address {
                    street1
                    city
                    province
                }
            }
            total
            lineItems(first: 20) {
                edges {
                    node {
                        id
                        name
                        quantity
                        unitPrice
                        totalPrice
                    }
                }
                totalCount
            }
        }
        userErrors {
            message
            path
        }
    }
}
"""

EDIT_JOB_MUTATION = """
mutation EditJob($jobId: EncodedId!, $input: JobEditInput!) {
    jobEdit(jobId: $jobId, input: $input) {
        job {
            id
            jobNumber
            title
            jobStatus
            instructions
            updatedAt
            total
            salesperson {
                id
                name {
                    full
                }
            }
        }
        userErrors {
            message
            path
        }
    }
}
"""

CLOSE_JOB_MUTATION = """
mutation CloseJob($jobId: EncodedId!, $input: JobCloseInput!) {
    jobClose(jobId: $jobId, input: $input) {
        job {
            id
            jobNumber
            title
            jobStatus
            closedAt
        }
        userErrors {
            message
            path
        }
    }
}
"""

REOPEN_JOB_MUTATION = """
mutation ReopenJob($jobId: EncodedId!) {
    jobReopen(jobId: $jobId) {
        job {
            id
            jobNumber
            title
            jobStatus
        }
        userErrors {
            message
            path
        }
    }
}
"""

CREATE_JOB_LINE_ITEMS_MUTATION = """
mutation CreateJobLineItems($jobId: EncodedId!, $input: JobCreateLineItemsInput!) {
    jobCreateLineItems(jobId: $jobId, input: $input) {
        job {
            id
            jobNumber
            total
            lineItems(first: 50) {
                edges {
                    node {
                        id
                        name
                        description
                        quantity
                        unitPrice
                        totalPrice
                        taxable
                    }
                }
                totalCount
            }
        }
        createdLineItems {
            id
            name
            description
            quantity
            unitPrice
            totalPrice
            taxable
        }
        userErrors {
            message
            path
        }
    }
}
"""

EDIT_JOB_LINE_ITEMS_MUTATION = """
mutation EditJobLineItems($jobId: EncodedId!, $input: JobEditLineItemsInput!) {
    jobEditLineItems(jobId: $jobId, input: $input) {
        job {
            id
            jobNumber
            total
        }
        modifiedLineItems {
            id
            name
            description
            quantity
            unitPrice
            totalPrice
            taxable
        }
        userErrors {
            message
            path
        }
    }
}
"""

DELETE_JOB_LINE_ITEMS_MUTATION = """
mutation DeleteJobLineItems($jobId: EncodedId!, $input: JobDeleteLineItemsInput!) {
    jobDeleteLineItems(jobId: $jobId, input: $input) {
        job {
            id
            jobNumber
            total
            lineItems(first: 50) {
                edges {
                    node {
                        id
                        name
                        totalPrice
                    }
                }
                totalCount
            }
        }
        deletedLineItems {
            id
            name
        }
        userErrors {
            message
            path
        }
    }
}
"""

# ============================================================================
# CLIENT MUTATIONS
# ============================================================================

CREATE_CLIENT_MUTATION = """
mutation CreateClient($input: ClientCreateInput!) {
    clientCreate(input: $input) {
        client {
            id
            firstName
            lastName
            companyName
            isCompany
            createdAt
            phones {
                number
                primary
            }
            emails {
                address
                primary
            }
            billingAddress {
                street1
                city
                province
                postalCode
            }
            properties {
                id
                address {
                    street1
                    city
                    province
                }
            }
        }
        userErrors {
            message
            path
        }
    }
}
"""

EDIT_CLIENT_MUTATION = """
mutation EditClient($clientId: EncodedId!, $input: ClientEditInput!) {
    clientEdit(clientId: $clientId, input: $input) {
        client {
            id
            firstName
            lastName
            companyName
            isCompany
            updatedAt
            phones {
                number
                primary
            }
            emails {
                address
                primary
            }
        }
        userErrors {
            message
            path
        }
    }
}
"""

ARCHIVE_CLIENT_MUTATION = """
mutation ArchiveClient($clientId: EncodedId!) {
    clientArchive(clientId: $clientId) {
        client {
            id
            firstName
            lastName
            companyName
            isArchived
        }
        userErrors {
            message
            path
        }
    }
}
"""

UNARCHIVE_CLIENT_MUTATION = """
mutation UnarchiveClient($clientId: EncodedId!) {
    clientUnarchive(clientId: $clientId) {
        client {
            id
            firstName
            lastName
            companyName
            isArchived
        }
        userErrors {
            message
            path
        }
    }
}
"""

# ============================================================================
# INVOICE MUTATIONS
# ============================================================================

CREATE_INVOICE_MUTATION = """
mutation CreateInvoice($input: InvoiceCreateInput!) {
    invoiceCreate(input: $input) {
        invoice {
            id
            invoiceNumber
            subject
            message
            invoiceStatus
            total
            subtotal
            taxTotal
            issuedDate
            dueDate
            createdAt
            client {
                id
                firstName
                lastName
                companyName
            }
            job {
                id
                jobNumber
                title
            }
            lineItems(first: 20) {
                edges {
                    node {
                        id
                        name
                        quantity
                        cost
                        total
                    }
                }
                totalCount
            }
        }
        userErrors {
            message
            path
        }
    }
}
"""

EDIT_INVOICE_MUTATION = """
mutation EditInvoice($invoiceId: EncodedId!, $input: InvoiceEditInput!) {
    invoiceEdit(invoiceId: $invoiceId, input: $input) {
        invoice {
            id
            invoiceNumber
            subject
            message
            invoiceStatus
            total
            subtotal
            taxTotal
            issuedDate
            dueDate
            updatedAt
        }
        userErrors {
            message
            path
        }
    }
}
"""

# ============================================================================
# ASSESSMENT MUTATIONS
# ============================================================================

CREATE_ASSESSMENT_MUTATION = """
mutation CreateAssessment($requestId: EncodedId!, $input: AssessmentCreateInput!) {
    assessmentCreate(requestId: $requestId, input: $input) {
        assessment {
            id
            startAt
            endAt
            instructions
            isComplete
            request {
                id
                title
                requestStatus
            }
            client {
                id
                firstName
                lastName
                companyName
            }
            property {
                id
                address {
                    street1
                    city
                    province
                }
            }
            assignedUsers(first: 10) {
                edges {
                    node {
                        id
                        name {
                            full
                        }
                    }
                }
            }
        }
        userErrors {
            message
            path
        }
    }
}
"""

EDIT_ASSESSMENT_MUTATION = """
mutation EditAssessment($assessmentId: EncodedId!, $input: AssessmentEditInput!) {
    assessmentEdit(assessmentId: $assessmentId, input: $input) {
        assessment {
            id
            startAt
            endAt
            instructions
            isComplete
            request {
                id
                title
            }
        }
        userErrors {
            message
            path
        }
    }
}
"""

COMPLETE_ASSESSMENT_MUTATION = """
mutation CompleteAssessment($assessmentId: EncodedId!) {
    assessmentComplete(assessmentId: $assessmentId) {
        assessment {
            id
            isComplete
            completedAt
            request {
                id
                title
                requestStatus
            }
        }
        userErrors {
            message
            path
        }
    }
}
"""

UNCOMPLETE_ASSESSMENT_MUTATION = """
mutation UncompleteAssessment($assessmentId: EncodedId!) {
    assessmentUncomplete(assessmentId: $assessmentId) {
        assessment {
            id
            isComplete
            request {
                id
                title
                requestStatus
            }
        }
        userErrors {
            message
            path
        }
    }
}
"""

DELETE_ASSESSMENT_MUTATION = """
mutation DeleteAssessment($assessmentId: EncodedId!) {
    assessmentDelete(assessmentId: $assessmentId) {
        deletedAssessmentId
        userErrors {
            message
            path
        }
    }
}
"""

# ============================================================================
# EXPENSE MUTATIONS
# ============================================================================

CREATE_EXPENSE_MUTATION = """
mutation CreateExpense($input: ExpenseCreateInput!) {
    expenseCreate(input: $input) {
        expense {
            id
            title
            description
            date
            total
            receiptUrl
            enteredBy {
                id
                name {
                    full
                }
            }
            reimbursableTo {
                id
                name {
                    full
                }
            }
            linkedJob {
                id
                jobNumber
                title
            }
            accountingCode {
                id
                code
                description
            }
            createdAt
        }
        userErrors {
            message
            path
        }
    }
}
"""

EDIT_EXPENSE_MUTATION = """
mutation EditExpense($expenseId: EncodedId!, $input: ExpenseEditInput!) {
    expenseEdit(expenseId: $expenseId, input: $input) {
        expense {
            id
            title
            description
            date
            total
            receiptUrl
            reimbursableTo {
                id
                name {
                    full
                }
            }
            linkedJob {
                id
                jobNumber
                title
            }
            updatedAt
        }
        userErrors {
            message
            path
        }
    }
}
"""

DELETE_EXPENSE_MUTATION = """
mutation DeleteExpense($expenseId: EncodedId!) {
    expenseDelete(expenseId: $expenseId) {
        deletedExpenseId
        userErrors {
            message
            path
        }
    }
}
"""

# ============================================================================
# VISIT LINE ITEM MUTATIONS
# ============================================================================

CREATE_VISIT_LINE_ITEMS_MUTATION = """
mutation CreateVisitLineItems($visitId: EncodedId!, $input: VisitCreateLineItemInput!) {
    visitCreateLineItems(visitId: $visitId, input: $input) {
        visit {
            id
            title
            job {
                id
                jobNumber
                total
            }
            lineItems(first: 50) {
                edges {
                    node {
                        id
                        name
                        description
                        quantity
                        unitPrice
                        totalPrice
                        taxable
                    }
                }
                totalCount
            }
        }
        userErrors {
            message
            path
        }
    }
}
"""

EDIT_VISIT_LINE_ITEMS_MUTATION = """
mutation EditVisitLineItems($visitId: EncodedId!, $input: VisitEditLineItemsInput!) {
    visitEditLineItems(visitId: $visitId, input: $input) {
        visit {
            id
            title
            job {
                id
                jobNumber
                total
            }
            lineItems(first: 50) {
                edges {
                    node {
                        id
                        name
                        description
                        quantity
                        unitPrice
                        totalPrice
                        taxable
                    }
                }
                totalCount
            }
        }
        userErrors {
            message
            path
        }
    }
}
"""

DELETE_VISIT_LINE_ITEMS_MUTATION = """
mutation DeleteVisitLineItems($visitId: EncodedId!, $input: VisitDeleteLineItemsInput!) {
    visitDeleteLineItems(visitId: $visitId, input: $input) {
        visit {
            id
            title
            job {
                id
                jobNumber
                total
            }
            lineItems(first: 50) {
                edges {
                    node {
                        id
                        name
                        totalPrice
                    }
                }
                totalCount
            }
        }
        userErrors {
            message
            path
        }
    }
}
"""
